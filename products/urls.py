from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('nuevo/', views.product_create, name='create'),
    path('<int:pk>/', views.product_detail, name='detail'),
    path('<int:pk>/editar/', views.product_edit, name='edit'),
    path('<int:pk>/eliminar/', views.product_delete, name='delete'),
    path('categorias/', views.category_list, name='categories'),
    path('categorias/nueva/', views.category_create_quick, name='category_create_quick'),
]
