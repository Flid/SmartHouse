import json
import logging
import os

import django
from celery import Celery
from django.conf import settings

from snailshell_cp.management.cluster_control.base import create_environment

app = Celery('snail_shell')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snailshell_cp.settings')

django.setup()
app.config_from_object('django.conf:settings')

logger = logging.getLogger(__name__)


def jload(data):
    return json.loads(data) if data else None


@app.task(name='snailshell_cp.deploy_container')
def deploy_container(deploy_job_id, portainer_client=None):
    from snailshell_cp.models import DeployJob
    deploy_job = DeployJob.objects.get(id=deploy_job_id)

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
