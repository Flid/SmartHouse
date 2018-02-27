from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Checks if admin user already exists, and creates if not.'

    def handle(self, *args, **options):
        login = settings.CONTROL_PANEL_ADMIN_USER

        if User.objects.filter(username=login).exists():
            self.stdout.write('Already exists')
            return

        User.objects.create_superuser(
            username=login,
            email=f'{login}@localhost',
            password=settings.CONTROL_PANEL_ADMIN_PASSWORD,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created user {login}',
        ))
