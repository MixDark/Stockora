from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_list, name='list'),
    path('pos/', views.pos_view, name='pos'),
    path('<int:pk>/', views.sale_detail, name='detail'),
    path('clientes/', views.customer_list, name='customers'),
    path('clientes/nuevo/', views.customer_create, name='customer_create'),
    path('clientes/<int:pk>/editar/', views.customer_edit, name='customer_edit'),
    path('clientes/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('clientes/<int:pk>/eliminar/', views.customer_delete, name='customer_delete'),
    # Cotizaciones
    path('cotizaciones/', views.quotation_list, name='quotations'),
    path('cotizaciones/nueva/', views.quotation_create, name='quotation_create'),
    path('cotizaciones/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('cotizaciones/<int:pk>/estado/', views.quotation_change_status, name='quotation_change_status'),
    path('cotizaciones/<int:pk>/convertir/', views.quotation_convert, name='quotation_convert'),
    path('cotizaciones/<int:pk>/eliminar/', views.quotation_delete, name='quotation_delete'),
    # Devoluciones
    path('devoluciones/', views.returns_list, name='returns'),
    path('<int:sale_pk>/devolucion/', views.return_create, name='return_create'),
    path('devoluciones/<int:pk>/', views.return_detail, name='return_detail'),
]
