from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# 1. User Roles
class Profile(models.Model):
    ROLE_CHOICES = (
        ('MANAGER', 'System Manager'),
        ('ADMIN', 'Administrator'),
        ('OFFICER', 'Traffic Officer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='OFFICER')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Default new users to OFFICER unless explicitly changed
        Profile.objects.create(user=instance, role='OFFICER')

# 2. Vehicle Owners
class Owner(models.Model):
    full_name = models.CharField(max_length=120)
    photo = models.ImageField(upload_to='owners/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

# 3. Traffic Cameras
class TrafficCamera(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.location})"

# 4. Vehicles
class Vehicle(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='vehicles', blank=True, null=True)
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.registration_number

# 4. Violations
class Violation(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
    )
    CATEGORY_CHOICES = (
        ('SPEEDING', 'Speeding'),
        ('RED_LIGHT', 'Red Light Violation'),
        ('ILLEGAL_PARKING', 'Illegal Parking'),
        ('WRONG_WAY', 'Wrong Way Driving'),
        ('OTHER', 'Other'),
    )
    OCR_STATUS_CHOICES = (
        ('NOT_RUN', 'Not Run'),
        ('SUCCESS', 'Plate Extracted'),
        ('FAILED', 'Extraction Failed'),
    )
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    manual_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Verified/Manual Plate")
    camera = models.ForeignKey(TrafficCamera, on_delete=models.CASCADE)
    violation_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    evidence = models.ImageField(upload_to='evidence/')
    description = models.TextField(blank=True, null=True)
    
    ocr_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="System OCR Attempt")
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name="OCR Confidence Score")
    ocr_status = models.CharField(max_length=10, choices=OCR_STATUS_CHOICES, default='NOT_RUN')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    detected_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_plate(self):
        if self.vehicle:
            return self.vehicle.registration_number
        return self.manual_plate or "Unknown"

    def __str__(self):
        return f"{self.get_plate()} - {self.get_violation_type_display()}"

# 5. Vehicle Sightings
class VehicleSighting(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    camera = models.ForeignKey(TrafficCamera, on_delete=models.CASCADE)
    sighting_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sighting_time']

    def __str__(self):
        return f"{self.vehicle.registration_number} at {self.camera.name}"