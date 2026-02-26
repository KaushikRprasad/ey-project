from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_invoice, name='upload_invoice'),
    path('list/', views.invoice_list, name='invoice_list'),
    path("view/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),
    path("delete/<int:invoice_id>/", views.delete_invoice, name="delete_invoice"),
    path("export/", views.export_invoices, name="export_invoices"),
    path("approve/<int:invoice_id>/", views.approve_invoice, name="approve_invoice"),
path("reject/<int:invoice_id>/", views.reject_invoice, name="reject_invoice"),
path("mark-paid/<int:invoice_id>/", views.mark_invoice_paid, name="mark_invoice_paid"),
 path("employees/", views.company_employees, name="company_employees"),
 path("approve-employee/<int:user_id>/", views.approve_employee, name="approve_employee"),
 path("reject-employee/<int:user_id>/", views.reject_employee, name="reject_employee"),
 path("add-employee/", views.add_employee_by_admin, name="add_employee_by_admin"),
]
