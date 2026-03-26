from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='home'),
    path('inventario/', views.inventory_report, name='inventory'),
    path('ventas/', views.sales_report, name='sales'),
    path('movimientos/', views.movements_report, name='movements'),
]
