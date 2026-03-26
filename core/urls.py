"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from accounts.views import password_reset_captcha

urlpatterns = [
    # Override password reset de allauth con captcha propio
    path('accounts/password/reset/', password_reset_captcha, name='account_reset_password'),
    path('accounts/', include('allauth.urls')),
    path('', include('accounts.urls', namespace='accounts')),
    path('productos/', include('products.urls', namespace='products')),
    path('inventario/', include('inventory.urls', namespace='inventory')),
    path('proveedores/', include('suppliers.urls', namespace='suppliers')),
    path('ventas/', include('sales.urls', namespace='sales')),
    path('reportes/', include('reports.urls', namespace='reports')),
    path('analitica/', include('analytics.urls', namespace='analytics')),
    path('notificaciones/', include('notifications.urls', namespace='notifications')),
    path('.well-known/<path:path>', serve, {
        'document_root': settings.BASE_DIR / 'static/.well-known',
        'show_indexes': False
    }),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
