import os
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .audit import log_action
from .decorators import admin_required, manager_required
from .models import User, AuditLog
from django.http import HttpResponse


@login_required
def dashboard(request):
    from products.models import Product, Category
    from inventory.models import StockItem, StockMovement, Warehouse
    from sales.models import Sale
    from notifications.models import StockAlert

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    threshold = getattr(settings, 'LOW_STOCK_DEFAULT_THRESHOLD', 10)

    total_products = Product.objects.filter(is_active=True).count()
    total_warehouses = Warehouse.objects.filter(is_active=True).count()
    low_stock_count = StockItem.objects.filter(quantity__lte=threshold, quantity__gt=0).count()
    out_of_stock_count = StockItem.objects.filter(quantity=0).count()
    monthly_sales = Sale.objects.filter(
        created_at__date__gte=thirty_days_ago, status=Sale.STATUS_COMPLETED
    ).count()
    recent_movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'performed_by'
    ).order_by('-created_at')[:10]
    active_alerts = StockAlert.objects.filter(
        status=StockAlert.STATUS_ACTIVE
    ).select_related('product', 'warehouse')[:5]
    unread_notifications_count = request.user.notifications.filter(is_read=False).count()
    low_stock_products = StockItem.objects.filter(
        quantity__lte=threshold, quantity__gt=0
    ).select_related('product', 'warehouse').order_by('quantity')[:8]
    top_categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0).order_by('-product_count')[:5]

    context = {
        'total_products': total_products,
        'total_warehouses': total_warehouses,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'monthly_sales': monthly_sales,
        'recent_movements': recent_movements,
        'active_alerts': active_alerts,
        'unread_notifications_count': unread_notifications_count,
        'low_stock_products': low_stock_products,
        'top_categories': top_categories,
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.phone      = request.POST.get('phone', '').strip()
        user.company    = request.POST.get('company', '').strip()
        if 'avatar' in request.FILES:
            avatar_file = request.FILES['avatar']
            _, ext = os.path.splitext(avatar_file.name)
            if ext.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                messages.error(request, 'Solo se permiten imágenes JPG, PNG, WEBP o GIF.')
                return redirect('accounts:profile')
            if avatar_file.size > 2 * 1024 * 1024:
                messages.error(request, 'La imagen no puede superar 2 MB.')
                return redirect('accounts:profile')
            user.avatar = avatar_file
        user.save()
        log_action(request, 'update', user, {'action': 'profile_update'})
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
@admin_required
def audit_log_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'accounts/audit_log.html', {'logs': logs})


@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'role_choices': User.ROLE_CHOICES,
    })


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        role      = request.POST.get('role', User.ROLE_READONLY)
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'El usuario "{username}" ya existe.')
        elif password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif role not in [r[0] for r in User.ROLE_CHOICES]:
            messages.error(request, 'Rol no válido.')
        else:
            try:
                validate_password(password1)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                user_obj = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password1,
                    role=role,
                )
                log_action(request, 'create', user_obj, {'role': role})
                messages.success(request, f'Usuario {user_obj.username} creado correctamente.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_reset_password(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            try:
                validate_password(password1, user=target)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                target.set_password(password1)
                target.must_change_password = True
                target.save()
                log_action(request, 'update', target, {'action': 'password_reset'})
                messages.success(request, f'Contraseña de {target.username} actualizada. El usuario deberá cambiarla al iniciar sesión.')
    return redirect('accounts:user_list')


@login_required
def force_change_password(request):
    """Fuerza al usuario a cambiar su contraseña antes de continuar."""
    if not request.user.must_change_password:
        return redirect('accounts:dashboard')
    # Consumir mensajes pendientes (ej. login/logout de allauth) para que no aparezcan aquí
    from django.contrib.messages import get_messages as _get_messages
    list(_get_messages(request))
    error = None
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            error = 'Las contraseñas no coinciden.'
        else:
            try:
                validate_password(password1, user=request.user)
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            else:
                request.user.set_password(password1)
                request.user.must_change_password = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                log_action(request, 'update', request.user, {'action': 'force_password_change'})
                return render(request, 'accounts/force_change_password.html', {'success': True})
    return render(request, 'accounts/force_change_password.html', {'error': error})


@login_required
@admin_required
def user_toggle_active(request, pk):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        if target == request.user:
            messages.error(request, 'No puedes desactivar tu propia cuenta.')
        else:
            target.is_active = not target.is_active
            target.save()
            estado = 'activado' if target.is_active else 'desactivado'
            log_action(request, 'update', target, {'is_active': target.is_active})
            messages.success(request, f'Usuario {target.username} {estado}.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_edit(request, pk):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        target.first_name = request.POST.get('first_name', '').strip()
        target.last_name = request.POST.get('last_name', '').strip()
        target.email = request.POST.get('email', '').strip()
        target.save()
        log_action(request, 'update', target, {'action': 'user_edit'})
        messages.success(request, f'Usuario {target.username} actualizado correctamente.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_delete(request, pk):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        if target == request.user:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
            return redirect('accounts:user_list')
        username = target.username
        try:
            log_action(request, 'delete', target)
            target.delete()
            messages.success(request, f'Usuario {username} eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar el usuario {username}.')
    return redirect('accounts:user_list')


@login_required
@admin_required
def user_change_role(request, pk):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=pk)
        new_role = request.POST.get('role', '')
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if new_role not in valid_roles:
            messages.error(request, 'Rol no válido.')
        else:
            target.role = new_role
            target.save()
            log_action(request, 'update', target, {'role': new_role})
            messages.success(request, f'Rol de {target.username} actualizado a {target.get_role_display()}.')
    return redirect('accounts:user_list')


def _generate_captcha(request):
    """Genera una operación aritmética simple y guarda la respuesta en sesión."""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    ops = [
        (f'{a} + {b}', a + b),
        (f'{a + b} - {b}', a),
        (f'{a} × {b}', a * b),
    ]
    question, answer = random.choice(ops)
    request.session['captcha_answer'] = answer
    return question


def password_reset_captcha(request):
    """Vista única de restablecimiento: paso 1 captcha, paso 2 nueva contraseña.

    El paso se determina exclusivamente por el campo oculto 'form_step' del POST.
    Un GET siempre muestra el paso 1 (captcha), sin depender de sesión.
    """
    if request.method == 'POST':
        form_step = request.POST.get('form_step', '1')

        # ── PASO 1: verificar captcha ──────────────────────────────────────────
        if form_step == '1':
            user_answer = request.POST.get('captcha_answer', '').strip()
            expected    = request.session.get('captcha_answer')
            try:
                captcha_ok = int(user_answer) == expected
            except (ValueError, TypeError):
                captcha_ok = False

            if not captcha_ok:
                return render(request, 'account/password_reset.html', {
                    'step': 1,
                    'captcha_question': _generate_captcha(request),
                    'captcha_error': 'Respuesta incorrecta. Inténtalo de nuevo.',
                })

            # Captcha correcto → mostrar directamente el paso 2
            request.session.pop('captcha_answer', None)
            return render(request, 'account/password_reset.html', {'step': 2})

        # ── PASO 2: cambiar contraseña ─────────────────────────────────────────
        if form_step == '2':
            username  = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            errors    = {}

            try:
                user_obj = User.objects.get(username=username, is_active=True)
            except User.DoesNotExist:
                errors['username'] = 'No existe ningún usuario activo con ese nombre.'

            if not errors:
                if len(password1) < 8:
                    errors['password1'] = 'La contraseña debe tener al menos 8 caracteres.'
                elif password1 != password2:
                    errors['password2'] = 'Las contraseñas no coinciden.'

            if not errors:
                user_obj.set_password(password1)
                user_obj.save()
                messages.success(request, 'Contraseña actualizada. Ya puedes iniciar sesión.')
                return redirect('account_login')

            return render(request, 'account/password_reset.html', {
                'step': 2,
                'errors': errors,
                'username_value': username,
            })

    # GET (o form_step no reconocido) → siempre paso 1
    # Limpiamos cualquier rastro de sesión anterior
    request.session.pop('captcha_verified', None)
    request.session.pop('captcha_answer', None)
    return render(request, 'account/password_reset.html', {
        'step': 1,
        'captcha_question': _generate_captcha(request),
    })


@login_required
@admin_required
def audit_log_export(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    lines = []
    for log in logs:
        user = log.user.username if log.user else 'Sistema'
        line = f"{log.timestamp:%Y-%m-%d %H:%M:%S}\t{user}\t{log.action}\t{log.model_name}\t{log.ip_address or '-'}\t{log.changes or '-'}"
        lines.append(line)
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="audit_log.txt"'
    return response

