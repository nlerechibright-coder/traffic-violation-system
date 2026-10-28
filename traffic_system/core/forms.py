from django import forms
from django.contrib.auth.models import User
from .models import TrafficCamera, Violation, Vehicle, Profile, Owner

class CameraForm(forms.ModelForm):
    class Meta:
        model = TrafficCamera
        fields = ['name', 'location', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class OfficerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Password")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user, defaults={'role': 'OFFICER'})
        return user

class OfficerEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class VehicleOwnerRegistrationForm(forms.Form):
    # Owner Details
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. John Doe'}))
    owner_photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), help_text="Upload a clear photo of the vehicle owner.")
    
    # Vehicle Details
    registration_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ABC-1234'}))
    vehicle_plate_image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), help_text="Upload a photo of the vehicle's license plate.")
    
    make = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    model = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    color = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

class ViolationForm(forms.ModelForm):
    manual_plate = forms.CharField(max_length=20, required=False, 
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC-1234'}))
    
    class Meta:
        model = Violation
        fields = ['vehicle', 'manual_plate', 'camera', 'violation_type', 'evidence', 'description']
        widgets = {
            'violation_type': forms.Select(attrs={'class': 'form-control'}),
            'camera': forms.Select(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'evidence': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['camera'].queryset = TrafficCamera.objects.filter(is_active=True)
        self.fields['camera'].empty_label = "Select an active camera"
        self.fields['camera'].required = True
        
    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        manual_plate = cleaned_data.get('manual_plate')
        if not vehicle and not manual_plate:
            raise forms.ValidationError("You must either select a registered vehicle or enter a manual plate number.")
        return cleaned_data

class ViolationManagementForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ['manual_plate', 'violation_type', 'status', 'description']
        widgets = {
            'manual_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'violation_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }