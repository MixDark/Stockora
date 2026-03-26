from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Notification, StockAlert


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'ok'})


@login_required
def stock_alerts(request):
    alerts = StockAlert.objects.filter(
        status=StockAlert.STATUS_ACTIVE
    ).select_related('product', 'warehouse').order_by('-created_at')
    return render(request, 'notifications/alerts.html', {'alerts': alerts})


@login_required
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

