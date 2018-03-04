import json

from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse
)
from django.views.decorators.csrf import csrf_exempt

from snailshell_cp.forms import CreateDeployJobForm
from snailshell_cp.models import PERMISSION_DEPLOY, AccessKey, DeployJob


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

    try:
        data = json.loads(request.body)
    except ValueError():
        return HttpResponseBadRequest(content='Invalid JSON')

    form = CreateDeployJobForm(data=data)

    if not form.is_valid():
        return HttpResponseBadRequest(
            content=json.dumps(form.errors),
            content_type='application/json',
        )

    _check_permissions(form.cleaned_data['access_key'], [PERMISSION_DEPLOY])

    deploy_job = DeployJob.objects.create(
        node=form.cleaned_data['node'],
        image_name=form.cleaned_data['image_name'],
        image_tag=form.cleaned_data['image_tag'],
    )

    return JsonResponse({'status': 'ok', 'job_id': deploy_job.id})
