from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from notifications.utils import create_notification
from notifications.email_utils import send_simple_mail
from .forms import RegisterForm, ProfileForm
from .models import CustomUser, Company, SubscriptionPlan
from invoices.models import Invoice
from expenses.models import Expense


# ===============================
# REGISTER (With 14 Day Trial)
# ===============================
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.first_name = request.POST.get("username") or "User"
            company_code = request.POST.get("company_code")

            # =====================================
            # JOIN EXISTING COMPANY
            # =====================================
            if company_code:
                try:
                    company = Company.objects.get(company_code=company_code.upper())
                except Company.DoesNotExist:
                    messages.error(request, "Invalid company code ❌")
                    return redirect("register")

                plan = company.plan

                # Count only employee seats (NOT admin)
                current_employees = CustomUser.objects.filter(
                    company=company,
                    role__in=["employee", "accountant"],
                    is_active=True
                ).count()

                # Calculate allowed limit
                if plan:
                    allowed_limit = plan.employee_limit + company.extra_employee_slots
                elif company.is_trial_active():
                    allowed_limit = 3
                else:
                    allowed_limit = 0

                if current_employees >= allowed_limit:
                    messages.error(request, "Employee limit reached. Upgrade plan 🚀")
                    return redirect("register")

                # 🔒 Require admin approval
                user.company = company
                selected_role = request.POST.get("role")
                if selected_role in ["employee", "accountant"]:
                    user.role = selected_role
                else:
                    user.role = "employee" # or detect from form if needed
                user.is_active = False  # 🔥 BLOCK LOGIN
                user.save()
                # 🔔 Notify Admins about new registration
                User = get_user_model()

                admins = User.objects.filter(
                    company=company,
                    role__in=["admin", "superadmin"],
                    is_active=True
                )

                for admin in admins:
                    # In-app notification
                    create_notification(
                        admin,
                        "New Employee Registration",
                        f"{user.username} registered as {user.role} and is waiting for approval."
                    )

                    # Email
                    send_simple_mail(
                        "New Employee Registration",
                        f"{user.username} registered as {user.role} and is waiting for approval.",
                        [admin.email]
                    )

                messages.success(
                    request,
                    "Account created successfully. Waiting for admin approval 🔒"
                )
                return redirect("login")

            # =====================================
            # CREATE NEW COMPANY (ADMIN)
            # =====================================
            else:
                company = Company.objects.create(
                    name=f"{user.username}'s Company",
                    trial_end_date=timezone.now().date() + timedelta(days=14)
                )

                user.company = company
                user.role = "admin"
                user.is_active = True  # Admin auto active
                user.save()

                messages.success(request, "Company created successfully 🎉")
                return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})
# ===============================
# LOGIN
# ===============================

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            if not user.is_active:
                messages.error(request, "Your account is pending admin approval 🔒")
                return redirect("login")

            login(request, user)

            if user.must_reset_password:
                return redirect("force_password_change")

            remember_me = request.POST.get("remember_me") == "on"
            if remember_me:
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return redirect("invoices:dashboard")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


# ===============================
# LOGOUT
# ===============================

def logout_view(request):
    logout(request)
    return redirect("login")


# ===============================
# PROFILE
# ===============================

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from invoices.models import Invoice
from expenses.models import Expense


@login_required
def profile(request):

    user = request.user
    password_form = PasswordChangeForm(user)

    if request.method == "POST":

        if "full_name" in request.POST:
            user.first_name = request.POST.get("full_name")
            user.email = request.POST.get("email")
            user.save()

            user.profile.phone = request.POST.get("phone")
            user.profile.address = request.POST.get("address")

            if request.FILES.get("profile_image"):
                user.profile.profile_pic = request.FILES.get("profile_image")

            user.profile.save()

            messages.success(request, "Profile updated successfully ✅")
            return redirect("profile")

    context = {
        "password_form": password_form,
        "total_invoices": Invoice.objects.filter(user=user).count(),
        "total_expenses": Expense.objects.filter(user=user).count(),
        "company_name": user.company.name if user.company else "No Company",
        "role": user.role,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password updated successfully.")
        return redirect("profile")

    return render(request, "accounts/change_password.html", {"form": form})


# ===============================
# UPGRADE PLAN PAGE
# ===============================

@login_required
def upgrade_plan(request):

    plans = SubscriptionPlan.objects.all()
    current_plan = request.user.company.plan

    return render(request, "accounts/upgrade.html", {
        "plans": plans,
        "current_plan": current_plan
    })


# ===============================
# ACTIVATE PLAN (30 Days)
# ===============================

@login_required
def activate_plan(request, plan_id):

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "Plan not found.")
        return redirect("upgrade_plan")

    company = request.user.company

    # 🔥 Assign plan
    company.plan = plan

    # 🔥 Set 30-day subscription
    company.subscription_end_date = timezone.now().date() + timedelta(days=30)

    # 🔥 Clear trial (optional but recommended)
    company.trial_end_date = None

    company.save()

    messages.success(request, f"{plan.name} plan activated successfully! 🚀")

    return redirect("invoices:dashboard")
from django.views.decorators.http import require_POST

@login_required
@require_POST
def add_employee_slot(request):

    company = request.user.company

    # 🔥 (Later integrate Razorpay here)
    company.extra_employee_slots += 1
    company.save()

    messages.success(request, "1 Employee slot added successfully 🎉")

    return redirect("invoices:company_employees")
@login_required
def force_password_change(request):

    if not request.user.must_reset_password:
        return redirect("invoices:dashboard")

    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.must_reset_password = False
        user.save()

        update_session_auth_hash(request, user)
        messages.success(request, "Password updated successfully ✅")

        return redirect("invoices:dashboard")

    return render(request, "accounts/force_password_change.html", {"form": form})