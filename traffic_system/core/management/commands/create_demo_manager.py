from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from core.models import Profile

class Command(BaseCommand):
    help = 'Creates or updates the dedicated demonstration management account'

    def handle(self, *args, **kwargs):
        username = 'traffick1'
        password = 'menny12345'
        
        # 1. Get or create the user safely
        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={
                'password': make_password(password),
                'is_superuser': False,
                'is_staff': False
            }
        )
        
        # 2. If the user already existed, ensure flags and password are correct
        if not user_created:
            user.password = make_password(password)
            user.is_superuser = False
            user.is_staff = False
            user.save()
            
        # 3. Get or create the profile and set it to MANAGER
        # This safely handles the profile created by the post_save signal
        profile, profile_created = Profile.objects.get_or_create(user=user)
        if profile.role != 'MANAGER':
            profile.role = 'MANAGER'
            profile.save()
            
        if user_created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created management user "{username}" with MANAGER role.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated existing user "{username}" to MANAGER role with secure password.'))