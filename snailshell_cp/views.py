import json
import logging
from http import HTTPStatus

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse
)
from django.views.decorators.csrf import csrf_exempt

from snailshell_cp.forms import CreateDeployJobForm
from snailshell_cp.models import PERMISSION_DEPLOY, AccessKey, DeployJob
from snailshell_cp.tasks import deploy_container

logger = logging.getLogger(__name__)


def _check_permissions(access_key, required_permissions):
    try:
        key = AccessKey.objects.get(value=access_key)
    except AccessKey.DoesNotExist:
        raise PermissionDenied()

    perms_available = set(key.permissions.split(','))

    missing_perms = set(required_permissions) - perms_available

    if missing_perms:
        raise PermissionDenied()


@csrf_exempt
def create_deploy_job(request):
    if request.method != 'POST':
        raise HttpResponseNotAllowed(['POST'])

    form = CreateDeployJobForm(data=request.POST)

    if not form.is_valid():
        return HttpResponseBadRequest(
            content=json.dumps(form.errors),
            content_type='application/json',
        )

    _check_permissions(form.cleaned_data['access_key'], [PERMISSION_DEPLOY])

    service = form.cleaned_data['service']

    if service.container_name in [
        settings.CONTROL_PANEL_CONTAINER_NAME,
        settings.CONTROL_PANEL_CELERY_MAIN_CONTAINER_NAME,
    ]:
        logger.error(
            'Service %s can\'t be deployed directly. Please deploy %s instead',
            service.container_name,
            settings.CONTROL_PANEL_CELERY_SERVICE_CONTAINER_NAME,
        )
        return JsonResponse(
            {
                'status': 'error',
                'reason': 'Undeployable service, read logs for details',
            }, status=HTTPStatus.BAD_REQUEST,
        )

    deploy_job = DeployJob.objects.create(
        service=service,
        image_tag=form.cleaned_data['image_tag'],
    )
    deploy_container.delay(deploy_job.id)

    return JsonResponse({'status': 'ok', 'job_id': deploy_job.id})
