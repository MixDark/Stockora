from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:pk>/leer/', views.mark_read, name='mark_read'),
    path('alertas/', views.stock_alerts, name='alerts'),
    path('no-leidas/', views.unread_count, name='unread_count'),
]
