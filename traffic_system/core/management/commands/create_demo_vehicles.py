from django.core.management.base import BaseCommand

from core.models import Owner, Vehicle


class Command(BaseCommand):
    help = 'Create sample registered vehicles and owners for demonstration purposes.'

    def handle(self, *args, **options):
        vehicles = [
            ('DEMO-ABC-123', 'Amelia Carter', 'Alice Motors', 'Aster', 'Silver', 'amelia.carter@example.com', '+1 555 104 2001', '12 Orchard Lane, Demo City'),
            ('DEMO-DEF-456', 'Noah Brooks', 'Briar Auto', 'Velora', 'Blue', 'noah.brooks@example.com', '+1 555 104 2002', '53 Cedar Avenue, Demo City'),
            ('DEMO-GHI-789', 'Priya Shah', 'Crestline Motors', 'Summit', 'Black', 'priya.shah@example.com', '+1 555 104 2003', '88 River Road, Demo City'),
            ('DEMO-JKL-012', 'Lucas Martin', 'Delta Drive', 'Orbit', 'Red', 'lucas.martin@example.com', '+1 555 104 2004', '17 Pine Street, Demo City'),
            ('DEMO-MNO-345', 'Sofia Nguyen', 'Echo Auto', 'Nova', 'White', 'sofia.nguyen@example.com', '+1 555 104 2005', '29 Maple Street, Demo City'),
            ('DEMO-PQR-678', 'Daniel Lewis', 'Foxtrot Garage', 'Trail', 'Green', 'daniel.lewis@example.com', '+1 555 104 2006', '44 Oak Hill, Demo City'),
            ('DEMO-STU-901', 'Mila Patel', 'Granite Motors', 'Comet', 'Grey', 'mila.patel@example.com', '+1 555 104 2007', '72 Willow Way, Demo City'),
            ('DEMO-VWX-234', 'Ethan Reed', 'Harbor Vehicles', 'Drift', 'Yellow', 'ethan.reed@example.com', '+1 555 104 2008', '91 Lantern Square, Demo City'),
            ('DEMO-YZA-567', 'Olivia Walker', 'Iron Peak Auto', 'Beacon', 'Purple', 'olivia.walker@example.com', '+1 555 104 2009', '31 Mill Road, Demo City'),
            ('DEMO-BCD-890', 'Henry Singh', 'Jetstream Motors', 'Ridge', 'Orange', 'henry.singh@example.com', '+1 555 104 2010', '62 Meadow Close, Demo City'),
        ]

        created_count = 0
        for registration_number, full_name, make, model, color, email, phone, address in vehicles:
            owner, _ = Owner.objects.get_or_create(
                full_name=full_name,
                defaults={'email': email, 'phone': phone, 'address': address},
            )
            vehicle, created = Vehicle.objects.get_or_create(
                registration_number=registration_number,
                defaults={'owner': owner, 'make': make, 'model': model, 'color': color},
            )
            if created:
                vehicle.owner = owner
                vehicle.make = make
                vehicle.model = model
                vehicle.color = color
                vehicle.save()
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} demo vehicles and owners.'))
