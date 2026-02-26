from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view   
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", login_view, name="root_login"),
    path("", include("invoices.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/force_password_change.html'
         ),
         name='password_reset_confirm'),
     # Password Reset Confirm (Set Password)
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/set_password.html',
        ),
        name='password_reset_confirm'
    ),

    # After successful password set
    path(
        'reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/set_password_complete.html'
        ),
        name='password_reset_complete'
    ),
    path("notifications/", include("notifications.urls")),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
