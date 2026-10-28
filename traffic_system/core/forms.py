from django import forms
from django.contrib.auth.models import User
from .models import TrafficCamera, Violation, Vehicle, Profile, Owner
from .utils import normalize_plate_number

class CameraForm(forms.ModelForm):
    class Meta:
        model = TrafficCamera
        fields = ['name', 'location', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class OfficerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

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

class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['full_name', 'photo', 'email', 'phone', 'address']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['owner', 'registration_number', 'make', 'model', 'color']

    def clean_registration_number(self):
        registration_number = normalize_plate_number(self.cleaned_data['registration_number'])
        if not registration_number:
            raise forms.ValidationError('Enter a valid registration number.')
        if self.instance.pk is None and Vehicle.objects.filter(registration_number__iexact=registration_number).exists():
            raise forms.ValidationError('This registration number is already registered.')
        return registration_number.upper()

class VehicleOwnerRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    photo = forms.ImageField(required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    registration_number = forms.CharField(max_length=20)
    make = forms.CharField(max_length=50, required=False)
    model = forms.CharField(max_length=50, required=False)
    color = forms.CharField(max_length=30, required=False)

    def clean_registration_number(self):
        registration_number = normalize_plate_number(self.cleaned_data['registration_number'])
        if not registration_number:
            raise forms.ValidationError('Enter a valid registration number.')
        if Vehicle.objects.filter(registration_number__iexact=registration_number).exists():
            raise forms.ValidationError('This registration number is already registered.')
        return registration_number.upper()

VehicleRegistrationForm = VehicleOwnerRegistrationForm

class ViolationForm(forms.ModelForm):
    manual_plate = forms.CharField(max_length=20, required=False, 
                                   widget=forms.TextInput(attrs={'placeholder': 'e.g., ABC-1234 (if not in system)'}))
    
    class Meta:
        model = Violation
        fields = ['vehicle', 'manual_plate', 'camera', 'violation_type', 'evidence', 'description']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['camera'].queryset = TrafficCamera.objects.filter(is_active=True)
        self.fields['camera'].empty_label = "Select an active camera"
        
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