from fabric.api import local, sudo
import os
import logging
from .base import cp_task
from django.conf import settings

logger = logging.getLogger(__name__)


@cp_task
def generate_local_ssh_key():
    ssh_root = os.path.expanduser('~/.ssh/')
    os.makedirs(ssh_root, mode=0o770, exist_ok=True)

    if os.path.exists(os.path.join(ssh_root, 'id_rsa')):
        logger.info('Shh key already exists - skipping.')
        return

    local('ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa')


@cp_task
def add_ssh_host(*, host, port, login, password):
    # TODO can be insecure. Copy the password to a local file
    # with o+r permissions and use the file with `-f` option.
    local(f'sshpass -p {password} ssh-copy-id {login}@{host} -p {port}')


def reset_docker():
    sudo(settings.CMD_UNINSTALL_DOCKER)
    sudo(settings.CMD_INSTALL_DOCKER)

    # Stop and remove all containers/images
    containers_running = sudo('docker ps -a -q')

    if containers_running:
        containers_running = ' '.join(containers_running.split())
        sudo(f'docker stop {containers_running}')
        sudo(f'docker rm {containers_running}')
