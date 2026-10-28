from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .decorators import role_required, management_required
from .models import Violation, TrafficCamera, Vehicle, VehicleSighting, Profile, Owner
from .forms import (
    CameraForm, OfficerCreationForm, OfficerEditForm, ViolationForm,
    ViolationManagementForm, VehicleOwnerRegistrationForm,
)
from .utils import normalize_plate_number, extract_plate_from_filename

def _match_vehicle_from_filename(filename):
    if not filename:
        return None, "No filename provided."
    plate_candidate = extract_plate_from_filename(filename)
    if not plate_candidate:
        return None, "Filename does not contain a recognizable plate number."
    matching_vehicle = Vehicle.objects.filter(registration_number__iexact=plate_candidate).first()
    if matching_vehicle:
        return matching_vehicle, f"Auto-matched vehicle {matching_vehicle.registration_number} from filename."
    return None, f"No vehicle found matching '{plate_candidate}' from filename."

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'profile'):
                if user.profile.role == 'MANAGER':
                    return redirect('management_dashboard')
                elif user.profile.role == 'ADMIN':
                    return redirect('admin_dashboard')
                else:
                    return redirect('officer_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@role_required(allowed_roles=['MANAGER', 'ADMIN', 'OFFICER'])
def dashboard_view(request):
    if request.user.profile.role == 'MANAGER':
        return redirect('management_dashboard')
    elif request.user.profile.role == 'ADMIN':
        return redirect('admin_dashboard')
    else:
        return redirect('officer_dashboard')

@management_required
def management_dashboard(request):
    context = {
        'total_cameras': TrafficCamera.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_violations': Violation.objects.count(),
        'pending_violations': Violation.objects.filter(status='PENDING').count(),
        'total_officers': User.objects.filter(profile__role='OFFICER').count(),
    }
    return render(request, 'core/management_dashboard.html', context)

@management_required
def management_camera_list(request):
    cameras = TrafficCamera.objects.all().order_by('-created_at')
    return render(request, 'core/management_camera_list.html', {'cameras': cameras})

@management_required
def management_camera_create(request):
    if request.method == 'POST':
        form = CameraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camera registered successfully.')
            return redirect('management_camera_list')
    else:
        form = CameraForm()
    return render(request, 'core/form_template.html', {'form': form, 'title': 'Register New Camera'})

@management_required
def management_camera_edit(request, pk):
    camera = get_object_or_404(TrafficCamera, pk=pk)
    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camera updated successfully.')
            return redirect('management_camera_list')
    else:
        form = CameraForm(instance=camera)
    return render(request, 'core/form_template.html', {'form': form, 'title': 'Edit Camera'})

@management_required
def management_officer_list(request):
    officers = User.objects.filter(profile__role='OFFICER').order_by('-date_joined')
    return render(request, 'core/management_officer_list.html', {'officers': officers})

@management_required
def management_officer_create(request):
    if request.method == 'POST':
        form = OfficerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Officer account created successfully.')
            return redirect('management_officer_list')
    else:
        form = OfficerCreationForm()
    return render(request, 'core/form_template.html', {'form': form, 'title': 'Create Traffic Officer'})

@management_required
def management_officer_edit(request, pk):
    officer = get_object_or_404(User, pk=pk, profile__role='OFFICER')
    if request.method == 'POST':
        form = OfficerEditForm(request.POST, instance=officer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Officer details updated successfully.')
            return redirect('management_officer_list')
    else:
        form = OfficerEditForm(instance=officer)
    return render(request, 'core/form_template.html', {'form': form, 'title': 'Edit Officer Details'})

@management_required
def management_violation_list(request):
    violations = Violation.objects.all().select_related('vehicle', 'camera').order_by('-detected_at')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    if search_query:
        violations = violations.filter(
            Q(vehicle__registration_number__icontains=search_query) |
            Q(manual_plate__icontains=search_query)
        )
    if status_filter:
        violations = violations.filter(status=status_filter)
    return render(request, 'core/management_violation_list.html', {
        'violations': violations, 'search_query': search_query, 'status_filter': status_filter
    })

@management_required
def management_violation_detail(request, pk):
    violation = get_object_or_404(Violation, pk=pk)
    if request.method == 'POST':
        form = ViolationManagementForm(request.POST, instance=violation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Violation record updated successfully.')
            return redirect('management_violation_list')
    else:
        form = ViolationManagementForm(instance=violation)
    latest_sighting = None
    if violation.vehicle:
        latest_sighting = VehicleSighting.objects.filter(vehicle=violation.vehicle).first()
    return render(request, 'core/management_violation_detail.html', {
        'violation': violation, 'form': form, 'latest_sighting': latest_sighting
    })

@management_required
def management_vehicle_list(request):
    vehicles = Vehicle.objects.select_related('owner').all().order_by('-id')
    search_query = request.GET.get('search', '')
    if search_query:
        vehicles = vehicles.filter(registration_number__icontains=search_query)
    return render(request, 'core/management_vehicle_list.html', {'vehicles': vehicles, 'search_query': search_query})

@management_required
def management_vehicle_register(request):
    if request.method == 'POST':
        form = VehicleOwnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            owner = Owner.objects.create(
                full_name=form.cleaned_data['full_name'],
                photo=form.cleaned_data.get('photo'),
                email=form.cleaned_data.get('email'),
                phone=form.cleaned_data.get('phone'),
                address=form.cleaned_data.get('address'),
            )
            vehicle = Vehicle.objects.create(
                owner=owner,
                registration_number=form.cleaned_data['registration_number'].upper(),
                make=form.cleaned_data.get('make') or '',
                model=form.cleaned_data.get('model') or '',
                color=form.cleaned_data.get('color') or '',
            )
            messages.success(request, f"Vehicle {vehicle.registration_number} was registered successfully.")
            return redirect('management_vehicle_list')
    else:
        form = VehicleOwnerRegistrationForm()
    return render(request, 'core/form_template.html', {'form': form, 'title': 'Register Vehicle & Owner'})

@management_required
def management_vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.select_related('owner'), pk=pk)
    sightings = VehicleSighting.objects.filter(vehicle=vehicle).order_by('-sighting_time')
    violations = Violation.objects.filter(vehicle=vehicle).order_by('-detected_at')
    return render(request, 'core/management_vehicle_detail.html', {
        'vehicle': vehicle, 'sightings': sightings, 'violations': violations
    })

@role_required(allowed_roles=['ADMIN'])
def admin_dashboard(request):
    context = {
        'total_cameras': TrafficCamera.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_violations': Violation.objects.count(),
        'pending_violations': Violation.objects.filter(status='PENDING').count(),
        'confirmed_violations': Violation.objects.filter(status='CONFIRMED').count(),
        'ocr_success_rate': Violation.objects.filter(ocr_status='SUCCESS').count(),
    }
    return render(request, 'core/admin_dashboard.html', context)

@role_required(allowed_roles=['ADMIN'])
def camera_list(request):
    return render(request, 'core/camera_list.html', {'cameras': TrafficCamera.objects.all().order_by('-created_at')})

@role_required(allowed_roles=['ADMIN'])
def camera_create(request):
    if request.method == 'POST':
        form = CameraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camera registered successfully.')
            return redirect('camera_list')
    return render(request, 'core/form_template.html', {'form': CameraForm(), 'title': 'Register New Camera'})

@role_required(allowed_roles=['ADMIN'])
def officer_create(request):
    if request.method == 'POST':
        form = OfficerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Traffic Officer account created successfully.')
            return redirect('admin_dashboard')
    return render(request, 'core/form_template.html', {'form': OfficerCreationForm(), 'title': 'Create Traffic Officer Account'})

@role_required(allowed_roles=['OFFICER'])
def officer_dashboard(request):
    pending = Violation.objects.filter(status='PENDING').order_by('-detected_at')
    return render(request, 'core/officer_dashboard.html', {'pending_violations': pending, 'total_pending': pending.count()})

@role_required(allowed_roles=['OFFICER', 'ADMIN'])
def violation_create(request):
    form = ViolationForm()
    ocr_message = None
    
    if request.method == 'POST':
        form = ViolationForm(request.POST, request.FILES)
        if form.is_valid():
            violation = form.save(commit=False)
            
            if form.cleaned_data.get('vehicle'):
                violation.vehicle = form.cleaned_data['vehicle']
            elif form.cleaned_data.get('manual_plate'):
                plate = normalize_plate_number(form.cleaned_data['manual_plate'])
                if plate:
                    violation.vehicle, _ = Vehicle.objects.get_or_create(registration_number=plate.upper())
            
            # FILENAME MATCHING ONLY (NO OCR TO PREVENT CRASHES)
            uploaded_file = request.FILES.get('evidence')
            if uploaded_file:
                matched_vehicle, match_message = _match_vehicle_from_filename(uploaded_file.name)
                if matched_vehicle:
                    violation.vehicle = matched_vehicle
                    violation.manual_plate = matched_vehicle.registration_number
                    ocr_message = f"Auto-matched: {match_message}"
                else:
                    ocr_message = f"Note: {match_message}. Please verify the plate manually."
            
            violation.save()
            
            if violation.vehicle:
                VehicleSighting.objects.create(
                    vehicle=violation.vehicle,
                    camera=violation.camera,
                    sighting_time=violation.detected_at
                )
            
            messages.success(request, 'Violation reported and saved successfully.')
            return redirect('officer_dashboard')
            
    return render(request, 'core/violation_form.html', {'form': form, 'ocr_message': ocr_message})

@role_required(allowed_roles=['OFFICER', 'ADMIN'])
def violation_detail(request, pk):
    violation = get_object_or_404(Violation.objects.select_related('vehicle__owner', 'camera'), pk=pk)
    latest_sighting = VehicleSighting.objects.filter(vehicle=violation.vehicle).first() if violation.vehicle else None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'CONFIRM':
            violation.status = 'CONFIRMED'
            violation.save()
            messages.success(request, 'Violation confirmed.')
        elif action == 'REJECT':
            violation.status = 'REJECTED'
            violation.save()
            messages.success(request, 'Violation rejected.')
        return redirect('officer_dashboard')
    return render(request, 'core/violation_detail.html', {'violation': violation, 'latest_sighting': latest_sighting})
