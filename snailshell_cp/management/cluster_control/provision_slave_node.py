from asyncio import sleep

from fabric.api import sudo
import logging
from django.conf import settings

from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.utils import reset_docker
from .base import cp_task, copy_configs

logger = logging.getLogger(__name__)


@cp_task
def provision_slave_node(*, name, hostname):
    """
    Connect to a slave node, setup Docker and connect it to the cluster.
    """

    reset_docker()

    has_opts = sudo('grep -E "^DOCKER_OPTS" /etc/default/docker')

    if not has_opts:
        sudo(f'echo "DOCKER_OPTS=\'-H tcp://0.0.0.0:{settings.DOCKERD_API_PORT}\'" >> /etc/default/docker ')
        sudo('systemctl restart docker')
        sleep(1)  # TODO

    portainer_client = PortainerClient(settings.PORTAINER_INTERNAL_URL)
    portainer_client.authenticate(
        settings.PORTAINER_ADMIN_USER,
        settings.PORTAINER_ADMIN_PASSWORD,
    )

    portainer_client.add_endpoint(
        name,
        f'tcp://{hostname}:{settings.DOCKERD_API_PORT}',
    )
