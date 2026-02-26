from django.urls import path
from  . import views

urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("add/", views.add_expense, name="add_expense"),
    path("delete/<int:expense_id>/", views.delete_expense, name="delete_expense"),  
    path("edit/<int:expense_id>/", views.edit_expense, name="expense_edit"),
    path("export/", views.export_expenses, name="export_expenses"),
    path("approve/<int:expense_id>/", views.approve_expense, name="approve_expense"),
path("reject/<int:expense_id>/", views.reject_expense, name="reject_expense"),
path("mark-paid/<int:expense_id>/", views.mark_expense_paid, name="mark_expense_paid"),
]
