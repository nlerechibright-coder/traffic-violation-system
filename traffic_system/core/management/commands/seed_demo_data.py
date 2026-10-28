from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profile, TrafficCamera, Vehicle, Owner

class Command(BaseCommand):
    help = 'Seeds the live database with demo data for presentation'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting demo data seeding...')

        # 1. Create or Update Manager Account
        user, created = User.objects.get_or_create(username='traffick1')
        user.set_password('menny12345')
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role != 'MANAGER':
            profile.role = 'MANAGER'
            profile.save()
        self.stdout.write(self.style.SUCCESS('✓ Manager account "traffick1" is ready.'))

        # 2. Create Demo Camera (Idempotent)
        camera, created = TrafficCamera.objects.get_or_create(
            name='Main St Junction',
            defaults={
                'location': 'Downtown City Center',
                'description': 'Primary intersection camera',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Demo camera created.'))

        # 3. Create Demo Owner and Vehicle (Idempotent)
        owner, _ = Owner.objects.get_or_create(
            full_name='John Doe',
            defaults={'email': 'john.doe@example.com'}
        )
        vehicle, created = Vehicle.objects.get_or_create(
            registration_number='DEMO-123',
            defaults={
                'owner': owner,
                'make': 'Toyota',
                'model': 'Camry',
                'color': 'Silver'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Demo vehicle created.'))
        
        self.stdout.write(self.style.SUCCESS('🎉 All demo data seeded successfully on the live database!'))