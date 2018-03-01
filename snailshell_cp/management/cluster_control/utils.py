from fabric.api import local
import os
import logging
from .base import cp_task

logger = logging.getLogger(__name__)


@cp_task
def generate_local_ssh_key():
    ssh_root = os.path.expanduser('~/.ssh/')
    os.makedirs(ssh_root, mode=0o660, exist_ok=True)

    if os.path.exists(os.path.join(ssh_root, 'id_rsa')):
        logger.info('Shh key already exists - skipping.')
        return

    local('ssh-keygen -t rsa')
