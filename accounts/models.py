from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario personalizado con roles."""

    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_WAREHOUSE = 'warehouse'
    ROLE_READONLY = 'readonly'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador'),
        (ROLE_MANAGER, 'Gestor'),
        (ROLE_WAREHOUSE, 'Almacenero'),
        (ROLE_READONLY, 'Solo lectura'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_READONLY)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    company = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_MANAGER)


class AuditLog(models.Model):
    """Registro de auditoría de todas las acciones del sistema."""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_EXPORT = 'export'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Creación'),
        (ACTION_UPDATE, 'Actualización'),
        (ACTION_DELETE, 'Eliminación'),
        (ACTION_LOGIN, 'Inicio de sesión'),
        (ACTION_LOGOUT, 'Cierre de sesión'),
        (ACTION_EXPORT, 'Exportación'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de auditoría'
        verbose_name_plural = 'Logs de auditoría'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user} - {self.action} - {self.model_name} ({self.timestamp:%d/%m/%Y %H:%M})'

