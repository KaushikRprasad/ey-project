from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("upgrade/", views.upgrade_plan, name="upgrade_plan"),
    path("activate/<int:plan_id>/", views.activate_plan, name="activate_plan"),
    path("add-slot/", views.add_employee_slot, name="add_employee_slot"),
    path("force-password-change/", views.force_password_change, name="force_password_change"),
]