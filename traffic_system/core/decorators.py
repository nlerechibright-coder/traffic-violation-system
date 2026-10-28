from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                if request.user.profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrap
    return decorator

def management_required(view_func):
    def wrap(request, *args, **kwargs):
        # Must be authenticated, have a profile, and specifically be a MANAGER
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.user.profile.role == 'MANAGER':
                return view_func(request, *args, **kwargs)
        # Redirect to the unified login if access is denied
        return redirect('login')
    return wrap