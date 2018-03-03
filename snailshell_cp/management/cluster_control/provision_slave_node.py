from fabric.api import task, sudo
from time import sleep
import logging
import os
from snailshell_cp.clients.portainer import PortainerClient
from .base import cp_task, copy_configs

logger = logging.getLogger(__name__)


@cp_task
def provision_slave_node(*, name, hostname):
    """
    Connect to a slave node, setup Docker and connect it to the cluster.
    """

    sudo('ls /')
