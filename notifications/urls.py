from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("clear/", views.clear_notifications, name="clear"),
    path("delete/<int:note_id>/", views.delete_notification, name="delete"),
]