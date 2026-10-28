from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Management URLs
    path('management/dashboard/', views.management_dashboard, name='management_dashboard'),
    path('management/cameras/', views.management_camera_list, name='management_camera_list'),
    path('management/cameras/new/', views.management_camera_create, name='management_camera_create'),
    path('management/cameras/<int:pk>/edit/', views.management_camera_edit, name='management_camera_edit'),
    path('management/officers/', views.management_officer_list, name='management_officer_list'),
    path('management/officers/new/', views.management_officer_create, name='management_officer_create'),
    path('management/officers/<int:pk>/edit/', views.management_officer_edit, name='management_officer_edit'),
    path('management/violations/', views.management_violation_list, name='management_violation_list'),
    path('management/violations/<int:pk>/', views.management_violation_detail, name='management_violation_detail'),
    path('management/vehicles/', views.management_vehicle_list, name='management_vehicle_list'),
    path('management/vehicles/new/', views.management_vehicle_register, name='management_vehicle_register'),
    path('management/vehicles/<int:pk>/', views.management_vehicle_detail, name='management_vehicle_detail'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/cameras/', views.camera_list, name='camera_list'),
    path('admin/cameras/new/', views.camera_create, name='camera_create'),
    path('admin/officers/new/', views.officer_create, name='officer_create'),
    
    # Officer URLs
    path('officer/dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('violations/new/', views.violation_create, name='violation_create'),
    path('violations/<int:pk>/', views.violation_detail, name='violation_detail'),
]