from django.contrib.auth.models import AbstractUser
from django.db import models


# ===============================
# SUBSCRIPTION PLAN MODEL
# ===============================

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    invoice_limit = models.IntegerField(default=10)
    expense_limit = models.IntegerField(default=10)
    employee_limit = models.IntegerField(default=1)

    allow_export = models.BooleanField(default=False)
    allow_ocr = models.BooleanField(default=False)
    allow_reports = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# ===============================
# COMPANY MODEL
# ===============================

from django.utils import timezone
from datetime import timedelta

import uuid
from django.db import models
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 NEW FIELD (Company Join Code)
    company_code = models.CharField(
    max_length=12,
    blank=True,
    null=True
)  

    plan = models.ForeignKey(
        'SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    extra_employee_slots = models.IntegerField(default=0)
    trial_end_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)

    # ===============================
    # AUTO GENERATE COMPANY CODE
    # ===============================
    def save(self, *args, **kwargs):
        if not self.company_code:
            # Generate 8-character unique uppercase code
            self.company_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    # ===============================
    # PLAN STATUS METHODS
    # ===============================
    def is_trial_active(self):
        return self.trial_end_date and self.trial_end_date >= timezone.now().date()

    def is_subscription_active(self):
        return self.subscription_end_date and self.subscription_end_date >= timezone.now().date()

    def is_expired(self):
        today = timezone.now().date()

        if self.subscription_end_date:
            return self.subscription_end_date < today

        if self.trial_end_date:
            return self.trial_end_date < today

        return True

    def __str__(self):
        return f"{self.name} ({self.company_code})"


# ===============================
# CUSTOM USER MODEL
# ===============================

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
    ("admin", "Admin"),
    ("accountant", "Accountant"),
    ("employee", "Employee"),

    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    first_login = models.BooleanField(default=True)
    must_reset_password = models.BooleanField(default=False)
    def __str__(self):
        return self.username
