from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.conf import settings
from snailshell_cp.models import Node
from fabric.api import execute
from snailshell_cp.management.cluster_control.utils import generate_local_ssh_key


class Command(BaseCommand):
    help = 'Create a default admin, local node etc'

    def handle(self, *args, **options):
        login = settings.CONTROL_PANEL_ADMIN_USER

        if User.objects.filter(username=login).exists():
            self.stdout.write('Already initialized')
            return

        User.objects.create_superuser(
            username=login,
            email=f'{login}@localhost',
            password=settings.CONTROL_PANEL_ADMIN_PASSWORD,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created user {login}',
        ))

        node = Node.objects.create(
            id=settings.PORTAINER_LOCAL_ENDPOINT_ID,
            name=settings.PORTAINER_LOCAL_ENDPOINT_NAME,
            # These fields are never used for the local node
            host='localhost',
            port=0,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created Node {node}',
        ))

        generate_local_ssh_key()