from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from expenses.models import Expense
from django.contrib.auth import get_user_model
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from accounts.decorators import role_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils.timezone import now
from .models import Expense
from django.contrib.auth import get_user_model
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required

@login_required
def expense_list(request):

    user = request.user
    company = user.company

    # ==============================
    # ROLE-BASED DATA ACCESS
    # ==============================

    if user.role in ["admin", "superadmin"]:
        expenses_qs = Expense.objects.filter(
            company=company
        )

    elif user.role == "accountant":
        expenses_qs = Expense.objects.filter(
            company=company,
            status__in=["approved", "paid"]
        )

    else:  # employee
        expenses_qs = Expense.objects.filter(
            company=company,
            user=user
        )

    expenses_qs = expenses_qs.order_by("-created_at")

    # ==============================
    # FILTERS
    # ==============================

    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    page_number = request.GET.get('page')

    if search:
        expenses_qs = expenses_qs.filter(
            Q(title__icontains=search) |
            Q(payment_method__icontains=search)
        )

    if category:
        expenses_qs = expenses_qs.filter(category=category)

    if status:
        expenses_qs = expenses_qs.filter(status=status)

    try:
        if min_amount:
            expenses_qs = expenses_qs.filter(amount__gte=float(min_amount))
        if max_amount:
            expenses_qs = expenses_qs.filter(amount__lte=float(max_amount))
    except ValueError:
        pass

    # ==============================
    # STATS
    # ==============================

    total_expense_amount = expenses_qs.aggregate(
        total=Sum('amount')
    )['total'] or 0

    pending_count = expenses_qs.filter(status="pending").count()
    rejected_count = expenses_qs.filter(status="rejected").count()

    # ==============================
    # PAGINATION
    # ==============================

    paginator = Paginator(expenses_qs, 5)
    expenses = paginator.get_page(page_number)

    context = {
        "expenses": expenses,
        "search": search,
        "category": category,
        "status": status,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "total_expense_amount": total_expense_amount,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
    }

    return render(request, "expenses/list.html", context)

@login_required
def add_expense(request):

    if request.method == "POST":

        title = request.POST.get("title")
        amount = request.POST.get("amount")
        category = request.POST.get("category")
        payment_method = request.POST.get("payment_method")
        notes = request.POST.get("notes")

        expense = Expense.objects.create(
            user=request.user,
            company=request.user.company,
            title=title,
            amount=amount,
            category=category,
            payment_method=payment_method,
            status='pending',
            notes=notes
        )

        # 🔥 Notify Admins
        if request.user.role in ["employee", "accountant"]:

            User = get_user_model()

            admins = User.objects.filter(
                company=request.user.company,
                role__in=["admin", "superadmin"],
                is_active=True
            )

            for admin in admins:
                create_notification(
                    admin,
                    "New Expense Submitted",
                    f"{request.user.username} submitted Expense '{expense.title}' for approval."
                )

                send_simple_mail(
                    "New Expense Submitted",
                    f"{request.user.username} submitted Expense '{expense.title}' for approval.",
                    [admin.email]
                )

        return redirect("expense_list")

    return render(request, "expenses/add.html")

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Expense


from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

@login_required
@role_required(["admin", "superadmin"])
def delete_expense(request, expense_id):

    if request.user.role not in ["admin", "superadmin"]:
        return HttpResponseForbidden("Not allowed.")

    expense = get_object_or_404(
        Expense,
        id=expense_id,
        company=request.user.company
    )

    expense.delete()
    return redirect("expense_list")
from django.shortcuts import render, get_object_or_404, redirect
from .models import Expense

from django.shortcuts import render, redirect
from .models import Expense
from django.shortcuts import render, get_object_or_404, redirect
from .models import Expense


def edit_expense(request, expense_id):  # ✅ MUST be expense_id
    expense = get_object_or_404(
    Expense,
    id=expense_id,
    company=request.user.company
)
    if request.method == "POST":

        if expense.status != "pending":
            messages.error(request, "This expense is locked ❌")
            return redirect("expenses:expense_detail", expense_id=expense.id)
    if request.method == "POST":
        expense.title = request.POST.get("title")
        expense.amount = request.POST.get("amount")
        expense.category = request.POST.get("category")
        expense.payment_method = request.POST.get("payment_method")
        expense.status = request.POST.get("status")
        expense.notes = request.POST.get("notes")
        expense.save()

        return redirect("expense_list")

    return render(request, "expenses/edit.html", {
        "expense": expense
    })
import csv
from django.http import HttpResponse
from django.db.models import Q
from .models import Expense


def export_expenses(request):
    expenses = Expense.objects.filter(
    company=request.user.company
)

    category = request.GET.get("category")
    status = request.GET.get("status")
    min_amount = request.GET.get("min_amount")
    max_amount = request.GET.get("max_amount")
    search = request.GET.get("search")

    # Apply same filters as list page
    if category:
        expenses = expenses.filter(category=category)

    if status:
        expenses = expenses.filter(status=status)

    if min_amount:
        expenses = expenses.filter(amount__gte=min_amount)

    if max_amount:
        expenses = expenses.filter(amount__lte=max_amount)

    if search:
        expenses = expenses.filter(
            Q(title__icontains=search) |
            Q(payment_method__icontains=search)
        )

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Title",
        "Category",
        "Date",
        "Amount",
        "Payment Method",
        "Status",
    ])

    for exp in expenses:
        writer.writerow([
            exp.title,
            exp.category,
            exp.created_at.strftime("%d-%m-%Y"),
            exp.amount,
            exp.payment_method,
            exp.status,
        ])

    return response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required

from django.utils import timezone

@login_required
@role_required(["admin", "superadmin"])
def approve_expense(request, expense_id):

    expense = get_object_or_404(
        Expense,
        id=expense_id,
        company=request.user.company
    )

    if expense.status == "pending":
        expense.status = "approved"
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()

        # 🔔 Notification
        create_notification(
            expense.user,
            "Expense Approved",
            f"Expense '{expense.title}' has been approved."
        )

        # ✉️ Email
        send_simple_mail(
            "Expense Approved",
            f"Your expense '{expense.title}' has been approved.",
            [expense.user.email]
        )

    return redirect("expense_list")

from django.utils import timezone
from django.contrib import messages

@login_required
@role_required(["admin", "superadmin"])
def reject_expense(request, expense_id):

    expense = get_object_or_404(
        Expense,
        id=expense_id,
        company=request.user.company
    )

    if expense.status == "pending":

        expense.status = "rejected"
        expense.rejected_by = request.user
        expense.rejected_at = timezone.now()

        # 🔥 Get rejection reason
        rejection_reason = request.POST.get("rejection_reason")

        if rejection_reason:
            expense.notes = f"REJECTED: {rejection_reason}"

        expense.save()

        # 🔔 Notification
        create_notification(
            expense.user,
            "Expense Rejected",
            f"Expense '{expense.title}' was rejected."
        )

        # ✉️ Email (Include reason)
        send_simple_mail(
            "Expense Rejected",
            f"Your expense '{expense.title}' was rejected.\n\nReason: {rejection_reason if rejection_reason else 'No reason provided.'}",
            [expense.user.email]
        )

        messages.success(request, "Expense rejected successfully ❌")

    return redirect("expense_list")
@login_required
@role_required(["accountant", "superadmin"])
def mark_expense_paid(request, expense_id):

    expense = get_object_or_404(
        Expense,
        id=expense_id,
        company=request.user.company
    )

    if expense.status == "approved":
        expense.status = "paid"
        expense.save()

    return redirect("expense_list")