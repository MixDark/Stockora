from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Stockora', {'fields': ('role', 'phone', 'avatar', 'company')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr', 'ip_address')
    list_filter = ('action', 'model_name')
    search_fields = ('user__username', 'model_name', 'object_repr')
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address')
    date_hierarchy = 'timestamp'

