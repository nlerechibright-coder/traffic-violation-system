import io
import tempfile
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from .models import TrafficCamera, Vehicle, Violation, Profile, Owner, VehicleSighting
from .forms import ViolationForm

def get_valid_image_file(name="test.jpg"):
    """Generates a fresh, valid 1x1 pixel JPEG file for testing."""
    file = io.BytesIO()
    image = Image.new('RGB', (1, 1), color='red')
    image.save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/jpeg")


class OwnerPhotoAndMediaWorkflowTest(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.client = Client()
        self.manager = User.objects.create_user(username="manager", password="pass123")
        self.manager.profile.role = "MANAGER"
        self.manager.profile.save()
        self.officer = User.objects.create_user(username="officer", password="pass123")
        self.camera = TrafficCamera.objects.create(name="Test Cam", location="Test Loc")

    def test_owner_photo_persists_and_is_displayed_for_filename_matched_vehicle(self):
        self.client.login(username="manager", password="pass123")
        registration_response = self.client.post(
            reverse("management_vehicle_register"),
            {
                "full_name": "Registered Owner",
                "email": "owner@example.test",
                "phone": "555-0100",
                "address": "Test address",
                "registration_number": "DEMO-ABC-123",
                "make": "Example",
                "model": "Roadster",
                "color": "Blue",
                "photo": get_valid_image_file("owner.jpg"),
            },
        )
        self.assertRedirects(registration_response, reverse("management_vehicle_list"))

        owner = Owner.objects.get(full_name="Registered Owner")
        vehicle = Vehicle.objects.get(registration_number="DEMOABC123")
        self.assertEqual(vehicle.owner, owner)
        self.assertTrue(owner.photo.name.startswith("owners/"))
        self.assertTrue(owner.photo.storage.exists(owner.photo.name))

        self.client.logout()
        self.assertEqual(self.client.get(owner.photo.url).status_code, 302)
        self.client.login(username="officer", password="pass123")
        violation_response = self.client.post(
            reverse("violation_create"),
            {
                "vehicle": str(vehicle.pk),
                "manual_plate": "",
                "camera": str(self.camera.pk),
                "violation_type": "SPEEDING",
                "evidence": get_valid_image_file("DEMO-ABC-123.jpg"),
                "description": "Filename match test",
            },
        )
        self.assertRedirects(violation_response, reverse("officer_dashboard"))

        violation = Violation.objects.get(description="Filename match test")
        self.assertEqual(violation.vehicle, vehicle)
        self.assertTrue(violation.evidence.name.startswith("evidence/"))
        self.assertNotEqual(violation.evidence.name, owner.photo.name)

        detail_response = self.client.get(reverse("violation_detail", args=[violation.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, owner.full_name)
        self.assertContains(detail_response, owner.email)
        self.assertContains(detail_response, owner.phone)
        self.assertContains(detail_response, owner.address)
        self.assertContains(detail_response, vehicle.registration_number)
        self.assertContains(detail_response, vehicle.make)
        self.assertContains(detail_response, owner.photo.url)
        self.assertContains(detail_response, violation.evidence.url)

        with override_settings(DEBUG=False):
            owner_image_response = self.client.get(owner.photo.url)
            evidence_image_response = self.client.get(violation.evidence.url)
        self.assertEqual(owner_image_response.status_code, 200)
        self.assertEqual(evidence_image_response.status_code, 200)
        self.assertEqual(owner_image_response["Content-Type"], "image/jpeg")
        self.assertEqual(evidence_image_response["Content-Type"], "image/jpeg")
        owner_image_response.close()
        evidence_image_response.close()

        vehicle_detail_response = self.client.get(
            reverse("management_vehicle_detail", args=[vehicle.pk])
        )
        self.assertEqual(vehicle_detail_response.status_code, 200)
        self.assertContains(vehicle_detail_response, owner.photo.url)

    def test_missing_owner_photo_uses_placeholder_and_unmatched_vehicle_has_no_owner_details(self):
        owner = Owner.objects.create(full_name="Owner Without Photo")
        vehicle = Vehicle.objects.create(
            owner=owner,
            registration_number="REGISTERED123",
        )
        violation = Violation.objects.create(
            vehicle=vehicle,
            camera=self.camera,
            violation_type="SPEEDING",
            evidence=get_valid_image_file("unmatched-evidence.jpg"),
        )
        self.client.login(username="officer", password="pass123")

        detail_response = self.client.get(reverse("violation_detail", args=[violation.pk]))
        self.assertContains(detail_response, "No owner photo uploaded")

        unmatched_violation = Violation.objects.create(
            manual_plate="NO-MATCH-123",
            camera=self.camera,
            violation_type="SPEEDING",
            evidence=get_valid_image_file("unmatched-evidence-2.jpg"),
        )
        unmatched_response = self.client.get(
            reverse("violation_detail", args=[unmatched_violation.pk])
        )
        self.assertNotContains(unmatched_response, owner.full_name)
        self.assertNotContains(unmatched_response, owner.photo.url if owner.photo else "owners/")

class UserModelAndSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        
    def test_profile_automatically_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.role, 'OFFICER')

class AccessControlTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username='officer', password='pass123')
        self.manager = User.objects.create_user(username='manager', password='pass123')
        self.manager.profile.role = 'MANAGER'
        self.manager.profile.save()
        self.admin = User.objects.create_superuser(username='admin', password='pass123')
        
    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('management_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
    def test_officer_cannot_access_management(self):
        self.client.login(username='officer', password='pass123')
        response = self.client.get(reverse('management_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
    def test_manager_can_access_management(self):
        self.client.login(username='manager', password='pass123')
        response = self.client.get(reverse('management_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_officer_can_access_officer_dashboard(self):
        self.client.login(username='officer', password='pass123')
        response = self.client.get(reverse('officer_dashboard'))
        self.assertEqual(response.status_code, 200)

class ViolationFormValidationTest(TestCase):
    def setUp(self):
        self.camera = TrafficCamera.objects.create(name="Test Cam", location="Test Loc")
        
    def test_form_fails_without_plate_or_vehicle(self):
        form = ViolationForm(
            data={
                'violation_type': 'SPEEDING', 
                'camera': str(self.camera.pk),
                'manual_plate': '',
                'description': 'Test'
            },
            files={'evidence': get_valid_image_file()}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_form_succeeds_with_manual_plate(self):
        form = ViolationForm(
            data={
                'violation_type': 'SPEEDING', 
                'camera': str(self.camera.pk),
                'manual_plate': 'ABC-123',
                'description': 'Test'
            },
            files={'evidence': get_valid_image_file()}
        )
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

class ViolationWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username='officer', password='pass123')
        self.camera = TrafficCamera.objects.create(name="Test Cam", location="Test Loc")
        
    def test_create_violation_and_sighting(self):
        self.client.login(username='officer', password='pass123')
        
        response = self.client.post(
            reverse('violation_create'),
            {
                'violation_type': 'SPEEDING',
                'camera': str(self.camera.pk),
                'manual_plate': 'NEW-999',
                'evidence': get_valid_image_file(),
                'description': 'Test violation'
            }
        )
        
        self.assertEqual(response.status_code, 302, f"Expected 302, got {response.status_code}.")
        self.assertTrue(Violation.objects.filter(manual_plate='NEW-999').exists())
        vehicle = Vehicle.objects.get(registration_number='NEW999')
        self.assertTrue(
            VehicleSighting.objects.filter(
                vehicle=vehicle,
                camera=self.camera,
            ).exists()
        )