from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.stock_list, name='stock'),
    path('movimientos/', views.movement_list, name='movements'),
    path('movimientos/nuevo/', views.movement_create, name='movement_create'),
    path('almacenes/', views.warehouse_list, name='warehouses'),
    path('almacenes/nuevo/', views.warehouse_create, name='warehouse_create'),
    path('almacenes/<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('almacenes/<int:pk>/editar/', views.warehouse_edit, name='warehouse_edit'),
    path('almacenes/<int:pk>/eliminar/', views.warehouse_delete, name='warehouse_delete'),
    path('stock/<int:pk>/editar/', views.stock_edit, name='stock_edit'),
    path('stock/<int:pk>/eliminar/', views.stock_item_delete, name='stock_item_delete'),
]
