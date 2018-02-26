from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Checks if admin user already exists, and creates if not.'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write('Already exists')
            return

        User.objects.create_superuser(
            username='admin',
            email='admin@localhost',
            password='admin',
        )

        self.stdout.write(self.style.SUCCESS(
            'Successfully created user admin:admin,'
            ' don\'t forget to change the password',
        ))
