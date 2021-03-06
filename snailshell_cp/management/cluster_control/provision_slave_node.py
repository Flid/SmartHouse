import logging

from django.conf import settings
from fabric.api import sudo

from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.utils import reset_docker

from .base import cp_task

logger = logging.getLogger(__name__)


@cp_task
def provision_slave_node(*, name, hostname, reinstall_docker=True):
    """
    Connect to a slave node, setup Docker and connect it to the cluster.
    Returns an ID of a newly created endpoint.
    """

    reset_docker(reinstall_docker=reinstall_docker)

    sudo(settings.ENV.CMD_DOCKER_EXTERNAL_IP.format(port=settings.ENV.DOCKERD_API_PORT))
    sudo(settings.ENV.CMD_DOCKER_RESTART)

    portainer_client = PortainerClient.get_internal_client()
    response = portainer_client.add_endpoint(
        name,
        f'tcp://{hostname}:{settings.ENV.DOCKERD_API_PORT}',
    )
    return {'entrypoint_id': response['Id']}
