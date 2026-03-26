from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """Solo usuarios con rol admin pueden acceder."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not request.user.is_admin:
            messages.error(request, 'Acceso restringido. Se requiere rol Administrador.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Solo usuarios con rol admin o manager pueden acceder."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not request.user.is_manager:
            messages.error(request, 'Acceso restringido. Se requiere rol Gestor o superior.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def warehouse_or_above(view_func):
    """Usuarios con rol admin, manager o warehouse pueden acceder."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from accounts.models import User
        if not request.user.is_authenticated:
            return redirect('account_login')
        if request.user.role not in (User.ROLE_ADMIN, User.ROLE_MANAGER, User.ROLE_WAREHOUSE):
            messages.error(request, 'Acceso restringido.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
