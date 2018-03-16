import logging
import os
from time import sleep
from uuid import uuid4

import django
from django.conf import settings
from fabric.api import local

from snailshell_cp.clients.portainer import PortainerClient
from snailshell_cp.management.cluster_control.utils import (
    HOST_PG_DIR,
    HOST_SSH_DIR,
    generate_local_ssh_key,
    jdump,
    reset_docker
)

from .base import CommandRunError, cp_task, create_environment

logger = logging.getLogger(__name__)


def _setup_portainer():
    local(  # start Portainer
        f'docker run -d '
        f'-p {settings.ENV.PORTAINER_PORT}:9000 --restart always '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'-v /opt/portainer:/data '
        f'--name {settings.ENV.PORTAINER_DOCKER_CONTAINER_NAME} '
        f'{settings.ENV.PORTAINER_IMAGE_NAME}:{settings.ENV.PORTAINER_IMAGE_TAG}',
    )

    sleep(2)  # TODO


def _get_portainer_client():
    logger.info('Initializing Portainer...')
    portainer_client = PortainerClient(settings.ENV.PORTAINER_EXTERNAL_URL)
    portainer_client.init_admin(
        settings.ENV.PORTAINER_ADMIN_USER,
        settings.ENV.PORTAINER_ADMIN_PASSWORD,
    )
    portainer_client.authenticate(
        settings.ENV.PORTAINER_ADMIN_USER,
        settings.ENV.PORTAINER_ADMIN_PASSWORD,
    )
    portainer_client.add_endpoint(
        settings.ENV.PORTAINER_LOCAL_ENDPOINT_NAME,
        settings.ENV.DOCKER_LOCAL_SOCKET_PATH,
    )
    return portainer_client


def _apply_migrations():
    attempts_left = 20

    while True:
        sleep(3)

        try:
            local('python3 manage.py migrate --noinput')
            break
        except CommandRunError as exc:
            logger.info(
                'Failed to apply migrations. Attempts left: %s',
                attempts_left,
            )

        attempts_left -= 1

        if attempts_left == 0:
            raise Exception('Can\'t connect to DB after 60 seconds')


def _setup_postgres(portainer_client):
    postgres_env = {
        'POSTGRES_USER': '$POSTGRES_USER',
        'POSTGRES_PASSWORD': '$POSTGRES_PASSWORD',
        'POSTGRES_DB': '$POSTGRES_DBNAME_CONTROL_PANEL',
    }
    host_config = {
        'PortBindings': {
            '5432/tcp': [{'HostPort': str(settings.ENV.POSTGRES_PORT)}],
        },
        'Binds': [
            f'{HOST_PG_DIR}:/var/lib/postgresql/data',
        ],
    }
    volumes = {'/var/lib/postgresql/data': {}}

    logger.info('Setting up Postgres...')
    portainer_client.create_image(
        settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.ENV.POSTGRES_IMAGE_NAME,
        settings.ENV.POSTGRES_IMAGE_TAG,
    )
    portainer_client.create_container(
        settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.ENV.POSTGRES_IMAGE_NAME,
        settings.ENV.POSTGRES_IMAGE_TAG,
        name=settings.ENV.POSTGRES_CONTAINER_NAME,
        request_data={
            'Env': create_environment(postgres_env, include_all=False),
            'HostConfig': host_config,
            'RestartPolicy': {'Name': 'unless-stopped'},
            'Volumes': volumes,
        },
    )
    portainer_client.start_container(
        settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        settings.ENV.POSTGRES_CONTAINER_NAME,
    )

    django.setup()

    logger.info('Filling DB with initial data...')
    from snailshell_cp.models import Node, AccessKey, PERMISSION_DEPLOY, Service
    from django.contrib.auth.models import User

    _apply_migrations()

    User.objects.create_superuser(
        username=settings.ENV.CONTROL_PANEL_ADMIN_USER,
        email=f'{settings.ENV.CONTROL_PANEL_ADMIN_USER}@localhost',
        password=settings.ENV.CONTROL_PANEL_ADMIN_PASSWORD,
    )
    logger.info(
        f'Successfully created user {settings.ENV.CONTROL_PANEL_ADMIN_USER}',
    )

    node = Node.objects.create(
        id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        name=settings.ENV.PORTAINER_LOCAL_ENDPOINT_NAME,
        # These fields are never used for the local node
        host='localhost',
        port=0,
    )
    logger.info(f'Successfully created Node {node}')

    AccessKey.objects.create(
        permissions=PERMISSION_DEPLOY,
        value=settings.ENV.CONTROL_PANEL_DEFAULT_DEPLOY_KEY or uuid4().hex,
    )

    Service.objects.create(
        node_id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        image_name=settings.ENV.POSTGRES_IMAGE_NAME,
        default_image_tag=settings.ENV.POSTGRES_IMAGE_TAG,
        container_name=settings.ENV.POSTGRES_CONTAINER_NAME,
        is_system_service=True,
        env_variables=jdump(postgres_env),
        host_config=jdump(host_config),
        volumes=jdump(volumes),
    )


def _setup_rabbitmq(portainer_client):
    logger.info('Setting up RabbitMQ...')
    from snailshell_cp.models import Service, DeployJob
    from snailshell_cp.tasks import deploy_container

    service = Service.objects.create(
        node_id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        image_name=settings.ENV.RABBITMQ_IMAGE_NAME,
        default_image_tag=settings.ENV.RABBITMQ_IMAGE_TAG,
        container_name=settings.ENV.RABBITMQ_CONTAINER_NAME,
        is_system_service=True,
        env_variables=jdump({
            'RABBITMQ_DEFAULT_USER': '$RABBITMQ_USER',
            'RABBITMQ_DEFAULT_PASS': '$RABBITMQ_PASSWORD',
        }),
        host_config=jdump({
            'PortBindings': {
                '5672/tcp': [
                    {'HostPort': str(settings.ENV.RABBITMQ_PORT)},
                ],
                '15672/tcp': [
                    {'HostPort': str(settings.ENV.RABBITMQ_MANAGEMENT_PORT)},
                ],
            },

        }),
    )

    deploy_job = DeployJob.objects.create(
        service=service,
    )
    deploy_container(
        deploy_job_id=deploy_job.id,
        portainer_client=portainer_client,
        is_provisioning=True,
    )


def _setup_control_panel(portainer_client):
    logger.info('Setting up Control Panel...')
    from snailshell_cp.models import Service, DeployJob
    from snailshell_cp.tasks import deploy_container

    container_sshdir = f'/home/{settings.ENV.CONTROL_PANEL_LINUX_USER}/.ssh'

    service_cp = Service.objects.create(
        node_id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        image_name=settings.ENV.CONTROL_PANEL_IMAGE_NAME,
        default_image_tag=settings.ENV.CONTROL_PANEL_IMAGE_TAG,
        container_name=settings.ENV.CONTROL_PANEL_CONTAINER_NAME,
        is_system_service=True,
        host_config=jdump({
            'Binds': [
                f'{HOST_SSH_DIR}:{container_sshdir}',
            ],
            'PortBindings': {
                f'8000/tcp': [
                    {'HostPort': str(settings.ENV.CONTROL_PANEL_PORT)},
                ],
            },
        }),
        volumes=jdump({container_sshdir: {}}),
        user_name=settings.ENV.CONTROL_PANEL_LINUX_USER,
    )
    deploy_job_cp = DeployJob.objects.create(
        service=service_cp,
    )
    deploy_container(
        deploy_job_id=deploy_job_cp.id,
        portainer_client=portainer_client,
        is_provisioning=True,
    )

    # Celery Main
    service_celery = Service.objects.create(
        node_id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        image_name=settings.ENV.CONTROL_PANEL_IMAGE_NAME,
        default_image_tag=settings.ENV.CONTROL_PANEL_IMAGE_TAG,
        container_name=settings.ENV.CONTROL_PANEL_CELERY_MAIN_CONTAINER_NAME,
        is_system_service=True,
        command=jdump(['./run_celery_main.sh']),
        user_name=settings.ENV.CONTROL_PANEL_LINUX_USER,
    )
    deploy_job_celery = DeployJob.objects.create(
        service=service_celery,
    )
    deploy_container(
        deploy_job_id=deploy_job_celery.id,
        portainer_client=portainer_client,
        is_provisioning=True,
    )

    # Celery Service
    service_celery = Service.objects.create(
        node_id=settings.ENV.PORTAINER_LOCAL_ENDPOINT_ID,
        image_name=settings.ENV.CONTROL_PANEL_IMAGE_NAME,
        default_image_tag=settings.ENV.CONTROL_PANEL_IMAGE_TAG,
        container_name=settings.ENV.CONTROL_PANEL_CELERY_SERVICE_CONTAINER_NAME,
        is_system_service=True,
        command=jdump(['./run_celery_service.sh']),
        user_name=settings.ENV.CONTROL_PANEL_LINUX_USER,
    )
    deploy_job_celery = DeployJob.objects.create(
        service=service_celery,
    )
    deploy_container(
        deploy_job_id=deploy_job_celery.id,
        portainer_client=portainer_client,
        is_provisioning=True,
    )


@cp_task
def provision_master_node(reinstall_docker=True):
    """
    Run on a main node once to set up all the services needed.
    WARNING: it wipes out everything, all unsaved data will be lost.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snailshell_cp.settings')

    reinstall_docker = (reinstall_docker not in (False, '0', 'false', 'False'))

    reset_docker(reinstall_docker=reinstall_docker, local_mode=True)
    local('rm -rf /opt/portainer/')
    local(f'rm -rf {HOST_PG_DIR}/*')

    _setup_portainer()
    portainer_client = _get_portainer_client()

    _setup_postgres(portainer_client)
    _setup_rabbitmq(portainer_client)
    _setup_control_panel(portainer_client)

    generate_local_ssh_key()
