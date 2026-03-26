from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='list'),
    path('nuevo/', views.supplier_create, name='create'),
    path('<int:pk>/', views.supplier_detail, name='detail'),
    path('<int:pk>/editar/', views.supplier_edit, name='edit'),
    path('<int:pk>/eliminar/', views.supplier_delete, name='delete'),
    path('ordenes/', views.purchase_order_list, name='orders'),
    path('ordenes/<int:pk>/editar/', views.purchase_order_edit, name='order_edit'),
    path('ordenes/<int:pk>/eliminar/', views.purchase_order_delete, name='order_delete'),
    path('ordenes/nueva/', views.purchase_order_create, name='order_create'),
    path('ordenes/<int:pk>/', views.purchase_order_detail, name='order_detail'),
]
