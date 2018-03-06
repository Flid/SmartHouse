import logging
from time import sleep

from django.conf import settings
from fabric.api import sudo

from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.utils import reset_docker

from .base import copy_configs, cp_task, get_all_settings_keys

logger = logging.getLogger(__name__)


@cp_task
def provision_master_node(reinstall_docker=True):
    """
    Run on a main node once to set up all the services needed.
    WARNING: it wipes out everything, all unsaved data will be lost.
    """
    reinstall_docker = (reinstall_docker not in (False, '0', 'false', 'False'))

    reset_docker(reinstall_docker=reinstall_docker)

    sudo('rm -rf /opt/portainer/')

    sudo(  # start Portainer
        f'docker run -d '
        f'-p {settings.PORTAINER_PORT}:9000 --restart always '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'-v /opt/portainer:/data '
        f'--name {settings.PORTAINER_DOCKER_CONTAINER_NAME} '
        f'{settings.PORTAINER_IMAGE_NAME}:{settings.PORTAINER_IMAGE_TAG}',
    )

    sleep(2)  # TODO

    logger.info('Initializing ')
    portainer_client = PortainerClient(settings.PORTAINER_EXTERNAL_URL)
    portainer_client.init_admin(
        settings.PORTAINER_ADMIN_USER,
        settings.PORTAINER_ADMIN_PASSWORD,
    )
    portainer_client.authenticate(
        settings.PORTAINER_ADMIN_USER,
        settings.PORTAINER_ADMIN_PASSWORD,
    )
    portainer_client.add_endpoint(
        settings.PORTAINER_LOCAL_ENDPOINT_NAME,
        settings.DOCKER_LOCAL_SOCKET_PATH,
    )

    # Postgres
    logger.info('Setting up Postgres...')
    portainer_client.create_image(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.POSTGRES_IMAGE_NAME,
        settings.POSTGRES_IMAGE_TAG,
    )
    portainer_client.create_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.POSTGRES_IMAGE_NAME,
        settings.POSTGRES_IMAGE_TAG,
        name=settings.POSTGRES_CONTAINER_NAME,
        request_data={
            'Env': copy_configs({
                'POSTGRES_USER': 'POSTGRES_USER',
                'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
                'POSTGRES_DB': 'POSTGRES_DBNAME_CONTROL_PANEL',
            }),
            'PortBindings': {
                '5432/tcp': [{'HostPort': str(settings.POSTGRES_PORT)}],
            },
            'RestartPolicy': {'Name': 'unless-stopped'},
        },
    )
    portainer_client.start_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.POSTGRES_CONTAINER_NAME,
    )

    # RabbitMQ
    logger.info('Setting up RabbitMQ...')
    portainer_client.create_image(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.RABBITMQ_IMAGE_NAME,
        settings.RABBITMQ_IMAGE_TAG,
    )
    portainer_client.create_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.RABBITMQ_IMAGE_NAME,
        settings.RABBITMQ_IMAGE_TAG,
        name=settings.RABBITMQ_CONTAINER_NAME,
        request_data={
            'Env': copy_configs({
                'RABBITMQ_DEFAULT_USER': 'RABBITMQ_USER',
                'RABBITMQ_DEFAULT_PASS': 'RABBITMQ_PASSWORD',
            }),
            'PortBindings': {
                '5672/tcp': [{'HostPort': str(settings.RABBITMQ_PORT)}],
                '15672/tcp': [{'HostPort': str(settings.RABBITMQ_MANAGEMENT_PORT)}],
            },
            'RestartPolicy': {'Name': 'unless-stopped'},
        },
    )
    portainer_client.start_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.RABBITMQ_CONTAINER_NAME,
    )

    # Control panel
    # Create a directory to store ssh configs of the container
    # TODO grop all configs on provisioning
    host_sshdir = '/opt/snailshell_cp/.ssh'
    container_sshdir = f'/home/{settings.CONTROL_PANEL_LINUX_USER}/.ssh'

    portainer_client.create_image(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.CONTROL_PANEL_IMAGE_NAME,
        settings.CONTROL_PANEL_IMAGE_TAG,
    )
    portainer_client.create_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.CONTROL_PANEL_IMAGE_NAME,
        settings.CONTROL_PANEL_IMAGE_TAG,
        name=settings.CONTROL_PANEL_CONTAINER_NAME,
        request_data={
            'Env': copy_configs({
                key: key for key in get_all_settings_keys()
            }),
            'PortBindings': {
                f'8000/tcp': [{'HostPort': str(settings.CONTROL_PANEL_PORT)}],
            },
            # TODO In future we might want to share host ssh key
            'Volumes': {container_sshdir: {}},
            'HostConfig': {
                'Binds': [
                    f'{host_sshdir}:{container_sshdir}',
                ],
            },
            'RestartPolicy': {'Name': 'unless-stopped'},
            'User': settings.CONTROL_PANEL_LINUX_USER,
        },
    )

    portainer_client.start_container(
        settings.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.CONTROL_PANEL_CONTAINER_NAME,
    )
