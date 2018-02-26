from fabric.api import run
from time import sleep
import logging
import os
from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.constants import CP_DOCKER_CONTAINER_NAME, \
    DOCKERHUB_IMAGE_NAME, DOCKER_LOCAL_SOCKET_PATH, \
    PORTAINER_LOCAL_ENDPOINT_NAME, PORTAINER_LOCAL_ENDPOINT_ID, \
    PORTAINER_DOCKER_CONTAINER_NAME

logger = logging.getLogger(__name__)


def provision_master_node():
    """
    Run on a main node once to set up all the services needed.
    WARNING: it wipes out everything, all unsaved data will be lost.
    """
    run('apt update')
    run('apt install lxc aufs-tools cgroup-lite apparmor docker.io curl python3')
    stop_portainer()
    run('rm -rf /opt/portainer/')
    start_portainer()
    sleep(1)  # TODO

    portainer_client = PortainerClient(os.environ['PORTAINER_BASE_URL'])
    portainer_client.init_admin(os.environ['PORTAINER_ADMIN_PASSWORD'])
    portainer_client.authenticate(os.environ['PORTAINER_ADMIN_PASSWORD'])
    portainer_client.add_endpoint(PORTAINER_LOCAL_ENDPOINT_NAME, DOCKER_LOCAL_SOCKET_PATH)

    cp_image = '{}/{}'.format(os.environ['DOCKERHUB_REPO'], DOCKERHUB_IMAGE_NAME)
    portainer_client.create_image(
        PORTAINER_LOCAL_ENDPOINT_ID,
        cp_image,
        os.environ['CONTROL_PANEL_TAG'],
    )
    portainer_client.create_container(
        PORTAINER_LOCAL_ENDPOINT_ID,
        cp_image,
        os.environ['CONTROL_PANEL_TAG'],
        name=CP_DOCKER_CONTAINER_NAME,
    )


def start_portainer():
    cmd = (
        'docker run -d -p 9000:9000 --restart always '
        '-v /var/run/docker.sock:/var/run/docker.sock '
        '-v /opt/portainer:/data '
        '--name {} '
        'portainer/portainer'
    ).format(PORTAINER_DOCKER_CONTAINER_NAME)
    run(cmd)


def stop_portainer():
    running_id = run(
        'docker ps --filter "name={}" --format "{{{{.ID}}}}"'.format(
            PORTAINER_DOCKER_CONTAINER_NAME,
        )
    )

    if running_id:
        run('docker stop {}'.format(running_id))
        run('docker rm {}'.format(running_id))
        logger.info(
            'Service %s has been stopped.',
            PORTAINER_DOCKER_CONTAINER_NAME,
        )
    else:
        logger.info(
            'Service %s is not running, skipping.',
            PORTAINER_DOCKER_CONTAINER_NAME,
        )
