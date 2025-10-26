import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure an admin user exists based on environment variables"

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        if not email or not password:
            self.stdout.write(self.style.WARNING("ADMIN_EMAIL or ADMIN_PASSWORD not set."))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(email=email, defaults={"role": User.Role.ADMIN})
        user.is_staff = True
        user.is_superuser = True
        user.role = User.Role.ADMIN
        user.username = user.username or email
        user.name = user.name or "Administrator"
        user.set_password(password)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created admin user {email}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated admin user {email}"))
