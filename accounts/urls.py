from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('perfil/', views.profile, name='profile'),
    path('auditoria/', views.audit_log_view, name='audit_log'),
    path('auditoria/exportar/', views.audit_log_export, name='audit_log_export'),
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/nuevo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/contrasena/', views.user_reset_password, name='user_reset_password'),
    path('usuarios/<int:pk>/activar/', views.user_toggle_active, name='user_toggle_active'),
    path('usuarios/<int:pk>/rol/', views.user_change_role, name='user_change_role'),
    path('usuarios/<int:pk>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:pk>/eliminar/', views.user_delete, name='user_delete'),
    path('cambiar-contrasena/', views.force_change_password, name='force_change_password'),
]
