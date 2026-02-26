from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Notification


@login_required
def notification_list(request):

    # 1️⃣ Mark unread as read
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    # 2️⃣ Fetch ALL notifications
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "notifications/list.html", {
        "notifications": notifications
    })

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def clear_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect("notifications:list")

from django.http import JsonResponse

@login_required
def delete_notification(request, note_id):
    Notification.objects.filter(id=note_id, user=request.user).delete()
    return JsonResponse({"status": "success"})