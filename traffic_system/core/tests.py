import io
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from .models import TrafficCamera, Vehicle, Violation, Profile
from .forms import ViolationForm

def get_valid_image_file():
    """Generates a fresh, valid 1x1 pixel JPEG file for testing."""
    file = io.BytesIO()
    image = Image.new('RGB', (1, 1), color='red')
    image.save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile("test.jpg", file.read(), content_type="image/jpeg")

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
        
    @patch('core.utils.process_image_for_plate')
    def test_create_violation_and_sighting(self, mock_ocr):
        # Mock the OCR function to prevent Windows access violation crashes during testing
        # and to ensure predictable, fast test behavior.
        mock_ocr.return_value = ('NEW-999', 0.95, 'SUCCESS')
        
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
        self.assertTrue(Vehicle.objects.filter(registration_number='NEW-999').exists())
        
        # Verify that the view actually attempted to call the OCR function
        mock_ocr.assert_called_once()