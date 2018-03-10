import json
import logging
import os

import django
from celery import Celery
from django.conf import settings

from snailshell_cp.management.cluster_control.base import create_environment
from snailshell_cp.models import DeployJob, Service

app = Celery('snail_shell')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snailshell_cp.settings')
django.setup()

app.config_from_object('django.conf:settings')

logger = logging.getLogger(__name__)


def jload(data):
    return json.loads(data) if data else None


def _deploy_container(deploy_job_id, portainer_client=None):
    deploy_job = DeployJob.objects.get(id=deploy_job_id)

    try:
        logger.info('Executing %s', deploy_job)
        service = deploy_job.service
        tag = deploy_job.image_tag or service.default_image_tag

        portainer_client.create_image(
            service.node.id,
            service.image_name,
            tag or service.default_image_tag,
        )

        portainer_client.create_container(
            service.node.id,
            service.image_name,
            tag,
            name=service.container_name,
            request_data={
                'Env': create_environment(jload(service.env_variables)),
                'Volumes': jload(service.volumes),
                'HostConfig': jload(service.host_config),
                'Cmd': jload(service.command),
                'RestartPolicy': {'Name': 'unless-stopped'},
                'User': service.user_name,
            },
        )

        portainer_client.start_container(
            service.node.id,
            service.container_name,
        )
    except Exception:
        deploy_job.status = DeployJob.FAILED
        deploy_job.save()
        raise

    else:
        deploy_job.status = DeployJob.FINISHED
        deploy_job.save()

    return deploy_job


@app.task(name='snailshell_cp.deploy_container')
def deploy_container(deploy_job_id, portainer_client=None):
    deploy_job = _deploy_container(
        deploy_job_id,
        portainer_client=portainer_client,
    )

    if deploy_job.service.container_name == settings.CONTROL_PANEL_CELERY_SERVICE_CONTAINER_NAME:  # noqa
        for srv_name in [
            settings.CONTROL_PANEL_CONTAINER_NAME,
            settings.CONTROL_PANEL_CELERY_MAIN_CONTAINER_NAME,
        ]:
            job_cp = DeployJob.objects.create(
                service=Service.objects.get(container_name=srv_name),
                image_tag=deploy_job.image_tag,
            )
            self_update.delay(job_cp)


@app.task(name='snailshell_cp.self_update')
def self_update(deploy_job_id):
    """
    Essentially the same as `deploy_container`,
    but is used to update control panel and main celery worker.
    """
    _deploy_container(deploy_job_id)
