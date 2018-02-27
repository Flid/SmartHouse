from fabric.api import run
from time import sleep
import logging
import os
from snailshell_cp.clients.portainer import PortainerClient

logger = logging.getLogger(__name__)


def load_env():
    keys = [
        'SECRET_KEY',
        'DOCKER_LOCAL_SOCKET_PATH',
        'DEBUG',
        'LOG_LEVEL',

        'CONTROL_PANEL_CONTAINER_NAME',
        'CONTROL_PANEL_IMAGE_NAME',
        'CONTROL_PANEL_IMAGE_TAG',

        'PORTAINER_LOCAL_ENDPOINT_NAME',
        'PORTAINER_LOCAL_ENDPOINT_ID',
        'PORTAINER_DOCKER_CONTAINER_NAME',
        'PORTAINER_IMAGE_NAME',
        'PORTAINER_IMAGE_TAG',
        'PORTAINER_PORT',
        'PORTAINER_ADMIN_PASSWORD',
        'PORTAINER_EXTERNAL_HOST',
        'PORTAINER_LOCAL_BASE_URL',

        'POSTGRES_IMAGE_NAME',
        'POSTGRES_IMAGE_TAG',
        'POSTGRES_CONTAINER_NAME',
        'POSTGRES_DBNAME_CONTROL_PANEL',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_PORT',

        'RABBITMQ_PORT',
        'RABBITMQ_MANAGEMENT_PORT',
        'RABBITMQ_CONTAINER_NAME',
        'RABBITMQ_IMAGE_NAME',
        'RABBITMQ_IMAGE_TAG',
        'RABBITMQ_USER',
        'RABBITMQ_PASSWORD',



    ]

    output = {}
    missing = []

    for key in keys:
        if key in os.environ:
            output[key] = os.environ[key]
        else:
            missing.append(key)

    if missing:
        raise Exception('Missing environment variables: {}'.format(
            ', '.join(missing)
        ))

    return output


def copy_configs(env, keys_map):
    return [
        f'{key_to}="{env[key_from]}"'
        for key_to, key_from in keys_map.items()
    ]


def provision_master_node():
    """
    Run on a main node once to set up all the services needed.
    WARNING: it wipes out everything, all unsaved data will be lost.
    """
    env = load_env()

    run('apt update')
    run('apt install lxc aufs-tools cgroup-lite apparmor docker.io curl python3')

    # Stop and remove all containers
    run('docker stop $(docker ps -a -q)')
    run('docker rm $(docker ps -a -q)')

    run('rm -rf /opt/portainer/')
    start_portainer(env)

    sleep(2)  # TODO

    logger.info('Initializing ')
    portainer_client = PortainerClient(env['PORTAINER_EXTERNAL_HOST'])
    portainer_client.init_admin(env['PORTAINER_ADMIN_PASSWORD'])
    portainer_client.authenticate(env['PORTAINER_ADMIN_PASSWORD'])
    portainer_client.add_endpoint(
        env['PORTAINER_LOCAL_ENDPOINT_NAME'],
        env['DOCKER_LOCAL_SOCKET_PATH'],
    )

    # Postgres
    logger.info('Setting up Postgres...')
    portainer_client.create_image(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['POSTGRES_IMAGE_NAME'],
        env['POSTGRES_IMAGE_TAG'],
    )
    portainer_client.create_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['POSTGRES_IMAGE_NAME'],
        env['POSTGRES_IMAGE_TAG'],
        name=env['POSTGRES_CONTAINER_NAME'],
        request_data={
            'Env': copy_configs(env, {
                'POSTGRES_USER': 'POSTGRES_USER',
                'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
                'POSTGRES_DB': 'POSTGRES_DBNAME_CONTROL_PANEL',
            }),
            'PortBindings': {
                '5432/tcp': [{'HostPort': env['POSTGRES_PORT']}],
            },
        }
    )
    portainer_client.start_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['POSTGRES_CONTAINER_NAME'],
    )

    # RabbitMQ
    logger.info('Setting up RabbitMQ...')
    portainer_client.create_image(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['RABBITMQ_IMAGE_NAME'],
        env['RABBITMQ_IMAGE_TAG'],
    )
    portainer_client.create_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['RABBITMQ_IMAGE_NAME'],
        env['RABBITMQ_IMAGE_TAG'],
        name=env['RABBITMQ_CONTAINER_NAME'],
        request_data={
            'Env': copy_configs(env, {
                'RABBITMQ_DEFAULT_USER': 'RABBITMQ_USER',
                'RABBITMQ_DEFAULT_PASS': 'RABBITMQ_PASSWORD',
            }),
            'PortBindings': {
                '5672/tcp': [{'HostPort': env['RABBITMQ_PORT']}],
                '15672/tcp': [{'HostPort': env['RABBITMQ_MANAGEMENT_PORT']}],
            },
        }
    )
    portainer_client.start_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['RABBITMQ_CONTAINER_NAME'],
    )

    # Control panel
    portainer_client.create_image(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['CONTROL_PANEL_IMAGE_NAME'],
        env['CONTROL_PANEL_IMAGE_TAG'],
    )
    portainer_client.create_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['CONTROL_PANEL_IMAGE_NAME'],
        env['CONTROL_PANEL_IMAGE_TAG'],
        name=env['CONTROL_PANEL_CONTAINER_NAME'],
        request_data={
            'Env': copy_configs(env, {
                'POSTGRES_USER': 'POSTGRES_USER',
                'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
                'POSTGRES_PORT': 'POSTGRES_PORT',
                'POSTGRES_DB': 'POSTGRES_DBNAME_CONTROL_PANEL',
                'PORTAINER_ADMIN_PASSWORD': 'PORTAINER_ADMIN_PASSWORD',
                'PORTAINER_BASE_URL': 'PORTAINER_LOCAL_BASE_URL',
                'LOG_LEVEL': 'LOG_LEVEL',
                'SECRET_KEY': 'SECRET_KEY',
                'DEBUG': 'DEBUG',
            }),
        }
    )
    portainer_client.start_container(
        env['PORTAINER_LOCAL_ENDPOINT_ID'],
        env['CONTROL_PANEL_CONTAINER_NAME'],
    )


def start_portainer(env):
    run(
        f'docker run -d '
        f'-p {env["PORTAINER_PORT"]}:9000 --restart always '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'-v /opt/portainer:/data '
        f'--name {env["PORTAINER_DOCKER_CONTAINER_NAME"]} '
        f'{env["PORTAINER_IMAGE_NAME"]}:{env["PORTAINER_IMAGE_TAG"]}'
    )
