

from re import search
from urllib import request
from notifications.utils import create_notification

from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from datetime import date
from django.contrib.auth.decorators import login_required
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from django.contrib.auth import get_user_model
from expenses.models import Expense
from .models import Invoice, Vendor
from .utilits import extract_text_from_image
from expenses.models import Expense
from django.contrib.auth import get_user_model
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from .models import Invoice, Vendor

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from .models import Invoice, Vendor
from accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from notifications.models import Notification

@login_required
def upload_invoice(request):

    if request.method == "POST":

        vendor_name = request.POST.get("vendor", "").strip()

        vendor, _ = Vendor.objects.get_or_create(
            name=vendor_name,
            company=request.user.company
        )

        invoice_number = request.POST.get("invoice_number")

        if Invoice.objects.filter(
            company=request.user.company,
            invoice_number=invoice_number
        ).exists():

            from django.contrib import messages
            messages.error(request, "Invoice number already exists ❌")
            return redirect("invoices:upload_invoice")

        inv_date = request.POST.get("date") or None
        invoice_file = request.FILES.get("invoice_file")

        payment_method = request.POST.get("payment_method")
        notes = request.POST.get("notes")

        amount_raw = request.POST.get("total_amount") or "0"
        amount_raw = str(amount_raw).replace(",", "").replace("₹", "").strip()

        try:
            total_amount = Decimal(amount_raw)
        except:
            total_amount = Decimal("0.00")

        tax_raw = request.POST.get("tax_amount", "0")
        tax_raw = str(tax_raw).replace(",", "").replace("₹", "").strip()

        try:
            tax_amount = Decimal(tax_raw)
        except:
            tax_amount = Decimal("0.00")

        company = request.user.company

        invoice = Invoice.objects.create(
            user=request.user,
            company=company,
            vendor=vendor,
            invoice_number=invoice_number,
            vendor_gst_number=request.POST.get("vendor_gst_number"),
            vendor_address=request.POST.get("vendor_address"),
            date=inv_date,
            total_amount=total_amount,
            tax_amount=tax_amount,
            payment_method=payment_method,
            status='pending',
            notes=notes,
            extracted_text=notes,
            file=invoice_file,
        )

        # 🔥 Notify Admins ONLY if employee/accountant
        if request.user.role in ["employee", "accountant"]:

            User = get_user_model()

            admins = User.objects.filter(
                company=company,
                role__in=["admin", "superadmin"],
                is_active=True
            )

            for admin in admins:
                create_notification(
                    admin,
                    "New Invoice Submitted",
                    f"{request.user.username} submitted Invoice {invoice.invoice_number} for approval."
                )

                send_simple_mail(
                    "New Invoice Submitted",
                    f"{request.user.username} submitted Invoice {invoice.invoice_number} for approval.",
                    [admin.email]
                )

        return redirect("invoices:invoice_list")

    return render(request, "invoices/upload.html")

from django.db.models import Q, Sum
from django.utils.timezone import now
from datetime import datetime
from .models import Invoice
from expenses.models import Expense
from .models import Vendor  # keep if already used
from accounts.decorators import role_required
  # Base queryset
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
@login_required
def dashboard(request):

    company = request.user.company
    user = request.user
    today = timezone.now().date()

    # ==============================
    # ROLE-BASED DATA ACCESS
    # ==============================

    if user.role in ["admin", "superadmin"]:
        invoices = Invoice.objects.filter(company=company)
        expenses = Expense.objects.filter(company=company)

    elif user.role == "accountant":
        invoices = Invoice.objects.filter(
            company=company,
            status__in=["approved", "paid"]
        )
        expenses = Expense.objects.filter(company=company)

    else:  # employee
        invoices = Invoice.objects.filter(
            company=company,
            user=user
        )
        expenses = Expense.objects.filter(
            company=company,
            user=user
        )

    # ==============================
    # DASHBOARD STATS
    # ==============================

    latest_invoices = invoices.order_by('-date')[:5]
    latest_expenses = expenses.order_by('-created_at')[:5]

    total_invoices = invoices.count()
    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    pending_invoice_approvals = invoices.filter(status="pending").count()
    rejected_invoices = invoices.filter(status="rejected").count()

    pending_expense_approvals = expenses.filter(status="pending").count()
    rejected_expenses = expenses.filter(status="rejected").count()

    total_pending_approvals = pending_invoice_approvals + pending_expense_approvals
    total_rejected_approvals = rejected_invoices + rejected_expenses


    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    latest_notification = Notification.objects.filter(
    user=request.user,
    is_read=False
    ).order_by("-created_at").first()
    context = {
        'total_invoices': total_invoices,
        'total_expense': total_expense,
        'latest_invoices': latest_invoices,
        'latest_expenses': latest_expenses,
        'total_pending_approvals': total_pending_approvals,
        'total_rejected_approvals': total_rejected_approvals,
        'current_plan': company.plan,
        'unread_notifications': unread_notifications,
        'latest_notification': latest_notification,   # 🔥 ADD THIS
    }

    return render(request, 'invoices/dashboard.html', context)

from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils.timezone import now
from .models import Invoice, Vendor

from django.contrib.auth.decorators import login_required

@login_required
def invoice_list(request):

    user = request.user
    company = user.company

    # ==============================
    # ROLE-BASED DATA ACCESS
    # ==============================

    if user.role in ["admin", "superadmin"]:
        invoices_qs = Invoice.objects.select_related("vendor").filter(
            company=company
        )

    elif user.role == "accountant":
        invoices_qs = Invoice.objects.select_related("vendor").filter(
            company=company,
            status__in=["approved", "paid"]
        )

    else:  # employee
        invoices_qs = Invoice.objects.select_related("vendor").filter(
            company=company,
            user=user
        )

    invoices_qs = invoices_qs.order_by("-date")

    # ==============================
    # FILTERS
    # ==============================

    search = request.GET.get("search", "")
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    max_amount = request.GET.get("max_amount") or ""
    status = request.GET.get("status", "")
    page_number = request.GET.get("page")

    if search:
        invoices_qs = invoices_qs.filter(
            Q(invoice_number__icontains=search) |
            Q(vendor__name__icontains=search)
        )

    if status:
        invoices_qs = invoices_qs.filter(status=status)

    if start_date:
        invoices_qs = invoices_qs.filter(date__gte=start_date)

    if end_date:
        invoices_qs = invoices_qs.filter(date__lte=end_date)

    if max_amount:
        try:
            invoices_qs = invoices_qs.filter(total_amount__lte=float(max_amount))
        except ValueError:
            pass

    # ==============================
    # STATS (BASED ON FILTERED DATA)
    # ==============================

    total_amount = invoices_qs.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    pending_count = invoices_qs.filter(status="pending").count()
    rejected_count = invoices_qs.filter(status="rejected").count()

    # ==============================
    # PAGINATION
    # ==============================

    paginator = Paginator(invoices_qs, 5)
    invoices = paginator.get_page(page_number)

    context = {
        "invoices": invoices,
        "total_amount": total_amount,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "search": search,
        "start_date": start_date,
        "end_date": end_date,
        "max_amount": max_amount,
        "status": status,
        "current_plan": company.plan,
    }

    return render(request, "invoices/list.html", context)

from django.shortcuts import redirect
from django.contrib import messages
from .models import Invoice

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
@role_required(["admin", "superadmin"])
def delete_invoice(request, invoice_id):

    if request.user.role not in ["admin", "superadmin"]:
        return HttpResponseForbidden("You don't have permission to delete.")

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        company=request.user.company
    )

    invoice.delete()
    return redirect("invoices:invoice_list")
@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        company=request.user.company
    )

    if request.method == "POST":

        # 🚫 LOCK IF NOT PENDING
        if invoice.status != "pending":
            from django.contrib import messages
            messages.error(request, "This invoice is locked and cannot be edited ❌")
            return redirect("invoices:invoice_detail", invoice_id=invoice.id)

        invoice.total_amount = request.POST.get("total_amount") or invoice.total_amount
        invoice.tax_amount = request.POST.get("tax_amount") or invoice.tax_amount
        invoice.payment_method = request.POST.get("payment_method")
        invoice.notes = request.POST.get("notes")

        invoice.save()

        from django.contrib import messages
        messages.success(request, "Invoice Updated Successfully ✅")

        return redirect("invoices:invoice_detail", invoice_id=invoice.id)

    return render(request, "invoices/detail.html", {"invoice": invoice})
import csv
from django.http import HttpResponse
from django.db.models import Q
from .models import Invoice

@login_required
def export_invoices(request):

    # 🔥 PLAN RESTRICTION CHECK (ADD HERE)
    if not request.user.company.plan or not request.user.company.plan.allow_export:
        invoices = Invoice.objects.filter(company=request.user.company)
        return render(request, "invoices/list.html", {
            "invoices": invoices,
            "show_upgrade_popup": True
        })

    invoices = Invoice.objects.select_related("vendor").filter(
        company=request.user.company
    )

    # Apply same filters as list page
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    search = request.GET.get("search")
    max_amount = request.GET.get("max_amount")

    if start_date:
        invoices = invoices.filter(date__gte=start_date)

    if end_date:
        invoices = invoices.filter(date__lte=end_date)

    if max_amount:
        invoices = invoices.filter(total_amount__lte=max_amount)

    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(vendor__name__icontains=search)
        )

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="invoices.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Invoice No",
        "Vendor",
        "Date",
        "Amount",
        "Tax",
        "Payment Method",
        "Status",
    ])

    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.vendor.name if inv.vendor else "",
            inv.date,
            inv.total_amount,
            inv.tax_amount,
            inv.payment_method,
            inv.status,
        ])

    return response
from django.utils import timezone

@login_required
@role_required(["admin", "superadmin"])
def approve_invoice(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        company=request.user.company
    )

    if invoice.status == "pending":
        invoice.status = "approved"
        invoice.approved_by = request.user
        invoice.approved_at = timezone.now()
        invoice.save()
    # 🔔 Notify invoice owner
    create_notification(
        invoice.user,
        "Invoice Approved",
        f"Invoice {invoice.invoice_number} has been approved."
    )

    send_simple_mail(
        "Invoice Approved",
        f"Your invoice {invoice.invoice_number} has been approved.",
        [invoice.user.email]
    )

    # 🔔 Notify accountants
    User = get_user_model()

    accountants = User.objects.filter(
        company=invoice.company,
        role="accountant",
        is_active=True
    )

    for acc in accountants:
        create_notification(
            acc,
            "Invoice Ready for Payment",
            f"Invoice {invoice.invoice_number} is approved and ready to mark paid."
        )

    return redirect("invoices:invoice_list")

@login_required
@role_required(["admin", "superadmin"])
def reject_invoice(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        company=request.user.company
    )

    if invoice.status == "pending":
        invoice.status = "rejected"
        invoice.rejected_by = request.user
        invoice.rejected_at = timezone.now()

        rejection_reason = request.POST.get("rejection_reason")

        if rejection_reason:
            invoice.notes = f"REJECTED: {rejection_reason}"

        invoice.save()

        # 🔔 Notification
        create_notification(
            invoice.user,
            "Invoice Rejected",
            f"Invoice {invoice.invoice_number} was rejected."
        )

        # ✉️ Email
        send_simple_mail(
            "Invoice Rejected",
            f"Your invoice {invoice.invoice_number} was rejected.\n\nReason: {rejection_reason if rejection_reason else 'No reason provided.'}",
            [invoice.user.email]
        )

    return redirect("invoices:invoice_detail", invoice_id=invoice.id)
@login_required
@role_required(["accountant", "superadmin"])
def mark_invoice_paid(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        company=request.user.company
    )

    if invoice.status == "approved":
        invoice.status = "paid"
        invoice.save()

    return redirect("invoices:invoice_list")
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

User = get_user_model()
@login_required
@role_required(["admin", "superadmin"])
def company_employees(request):

    company = request.user.company
    plan = company.plan

    employees = User.objects.filter(company=company).order_by("date_joined")

    # Count only employee seats
    # Count ONLY approved seat users
    employee_count = User.objects.filter(
        company=company,
        role__in=["employee", "accountant"],
        is_active=True
    ).count()
    pending_count = User.objects.filter(
        company=company,
        is_active=False
    ).count()
    # Determine limit
    if plan:
        allowed_limit = plan.employee_limit + company.extra_employee_slots
    elif company.is_trial_active():
        allowed_limit = 3
    else:
        allowed_limit = 0

    limit_reached = employee_count >= allowed_limit
    
    return render(request, "invoices/employees.html", {
        "employees": employees,
        "employee_count": employee_count,
        "allowed_limit": allowed_limit,
        "limit_reached": limit_reached,
        "pending_count": pending_count,
    })

@login_required
@role_required(["admin", "superadmin"])
def approve_employee(request, user_id):

    employee = get_object_or_404(
        User,
        id=user_id,
        company=request.user.company
    )

    employee.is_active = True
    employee.save()

    # 🔔 In-app notification
    create_notification(
        employee,
        "Account Approved",
        "Your account has been approved by admin. You can now login."
    )

    # 📧 Email
    send_simple_mail(
        "Your Account Has Been Approved 🎉",
        "Your account has been approved by admin. You can now login.",
        [employee.email]
    )

    messages.success(request, "Employee approved successfully ✅")

    return redirect("invoices:company_employees")
@login_required
@role_required(["admin", "superadmin"])
def reject_employee(request, user_id):

    employee = get_object_or_404(
        User,
        id=user_id,
        company=request.user.company
    )

    # 🔔 In-app notification BEFORE delete
    create_notification(
        employee,
        "Account Rejected",
        "Your registration request has been rejected by admin."
    )

    # 📧 Email
    send_simple_mail(
        "Your Account Registration Was Rejected",
        "Your registration request has been rejected by admin.\n\nPlease contact the administrator for more details.",
        [employee.email]
    )

    employee.delete()  # Remove after notifying

    messages.success(request, "Employee rejected and removed ❌")

    return redirect("invoices:company_employees")
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

User = get_user_model()

@login_required
@role_required(["admin", "superadmin"]) 
def add_employee_by_admin(request):

    company = request.user.company

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        role = request.POST.get("role")

        # Seat check (only active users count)
        employee_count = User.objects.filter(
            company=company,
            role__in=["employee", "accountant"],
            is_active=True
        ).count()

        if company.plan:
            allowed_limit = company.plan.employee_limit + company.extra_employee_slots
        elif company.is_trial_active():
            allowed_limit = 3
        else:
            allowed_limit = 0

        if employee_count >= allowed_limit:
            messages.error(request, "Seat limit reached 🚀")
            return redirect("invoices:company_employees")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email
        )

        user.company = company
        user.role = role
        user.is_active = True
        user.set_unusable_password()
        user.save()

        # 🔥 Generate secure password setup link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = request.build_absolute_uri(
            reverse("password_reset_confirm", kwargs={
                "uidb64": uid,
                "token": token
            })
        )

        # 🔥 Email content (HTML + Text)
        subject = "You're invited to FinSight 🚀"

        context = {
            "username": username,
            "company": company.name,
            "reset_link": reset_link,
        }

        text_content = render_to_string(
            "emails/invite_employee.txt",
            context
        )

        html_content = render_to_string(
            "emails/invite_employee.html",
            context
        )

        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        messages.success(request, "Employee invited successfully ✅")

        return redirect("invoices:company_employees")

    return render(request, "invoices/add_employee.html")
def new_dashboard(request):
    return render(request, "dashboard/new.html")


def old_dashboard(request):
    return render(request, "dashboard/main.html")

