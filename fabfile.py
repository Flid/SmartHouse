from fabric.api import run
from time import sleep
import logging
import os
from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.constants import CP_CONTAINER_NAME, \
    DOCKERHUB_IMAGE_NAME, DOCKER_LOCAL_SOCKET_PATH, \
    PORTAINER_LOCAL_ENDPOINT_NAME, PORTAINER_LOCAL_ENDPOINT_ID, \
    PORTAINER_DOCKER_CONTAINER_NAME, POSTGRES_IMAGE_NAME, POSTGRES_IMAGE_TAG, \
    POSTGRES_CONTAINER_NAME

logger = logging.getLogger(__name__)


def provision_master_node():
    """
    Run on a main node once to set up all the services needed.
    WARNING: it wipes out everything, all unsaved data will be lost.
    """
    CONTROL_PANEL_TAG = os.environ['CONTROL_PANEL_TAG']
    DOCKERHUB_REPO = os.environ['DOCKERHUB_REPO']
    PORTAINER_ADMIN_PASSWORD = os.environ['PORTAINER_ADMIN_PASSWORD']
    PORTAINER_BASE_URL = os.environ['PORTAINER_BASE_URL']
    POSTGRES_USER = os.environ['POSTGRES_USER']
    POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
    POSTGRES_PORT = os.environ['POSTGRES_PORT']
    POSTGRES_DBNAME_CONTROL_PANEL = os.environ['POSTGRES_DBNAME_CONTROL_PANEL']
    LOG_LEVEL = os.environ['LOG_LEVEL']
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = os.environ['DEBUG']

    run('apt update')
    run('apt install lxc aufs-tools cgroup-lite apparmor docker.io curl python3')

    # Stop and remove all containers
    run('docker stop $(docker ps -a -q)')
    run('docker rm $(docker ps -a -q)')

    run('rm -rf /opt/portainer/')
    start_portainer()
    sleep(2)  # TODO

    portainer_client = PortainerClient(PORTAINER_BASE_URL)
    portainer_client.init_admin(PORTAINER_ADMIN_PASSWORD)
    portainer_client.authenticate(PORTAINER_ADMIN_PASSWORD)
    portainer_client.add_endpoint(PORTAINER_LOCAL_ENDPOINT_NAME, DOCKER_LOCAL_SOCKET_PATH)

    # Postgres
    portainer_client.create_image(
        PORTAINER_LOCAL_ENDPOINT_ID,
        POSTGRES_IMAGE_NAME,
        POSTGRES_IMAGE_TAG,
    )
    portainer_client.create_container(
        PORTAINER_LOCAL_ENDPOINT_ID,
        POSTGRES_IMAGE_NAME,
        POSTGRES_IMAGE_TAG,
        name=POSTGRES_CONTAINER_NAME,
        request_data={
            'Env': [
                'POSTGRES_USER="{}"'.format(POSTGRES_USER),
                'POSTGRES_PASSWORD="{}"'.format(POSTGRES_PASSWORD),
                'POSTGRES_DB="{}"'.format(POSTGRES_DBNAME_CONTROL_PANEL),
            ],
            'PortBindings': {
                '5432/tcp': [{'HostPort': POSTGRES_PORT}],
            },
        }
    )
    portainer_client.start_container(
        PORTAINER_LOCAL_ENDPOINT_ID,
        POSTGRES_CONTAINER_NAME,
    )
    sleep(5)  # TODO

    # Control panel
    cp_image = '{}/{}'.format(DOCKERHUB_REPO, DOCKERHUB_IMAGE_NAME)
    portainer_client.create_image(
        PORTAINER_LOCAL_ENDPOINT_ID,
        cp_image,
        CONTROL_PANEL_TAG,
    )
    portainer_client.create_container(
        PORTAINER_LOCAL_ENDPOINT_ID,
        cp_image,
        CONTROL_PANEL_TAG,
        name=CP_CONTAINER_NAME,
        request_data={
            'Env': [
                'POSTGRES_USER="{}"'.format(POSTGRES_USER),
                'POSTGRES_PASSWORD="{}"'.format(POSTGRES_PASSWORD),
                'POSTGRES_PORT="{}"'.format(POSTGRES_PORT),
                'POSTGRES_DB="{}"'.format(POSTGRES_DBNAME_CONTROL_PANEL),
                'PORTAINER_ADMIN_PASSWORD="{}"'.format(PORTAINER_ADMIN_PASSWORD),
                # TODO should be `localhost`, but will work for now
                'PORTAINER_BASE_URL="{}"'.format(PORTAINER_BASE_URL),
                'LOG_LEVEL="{}"'.format(LOG_LEVEL),
                'SECRET_KEY="{}"'.format(SECRET_KEY),
                'DEBUG="{}"'.format(DEBUG),
            ],
        }
    )
    portainer_client.start_container(
        PORTAINER_LOCAL_ENDPOINT_ID,
        CP_CONTAINER_NAME,
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
