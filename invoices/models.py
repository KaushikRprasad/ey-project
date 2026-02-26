from django.db import models
from django.conf import settings
from accounts.models import Company


class Vendor(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE
    )

    invoice_number = models.CharField(max_length=100)

    # 🔥 NEW FIELDS
    vendor_gst_number = models.CharField(max_length=20, blank=True, null=True)
    vendor_address = models.TextField(blank=True, null=True)

    date = models.DateField()

    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=50, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    notes = models.TextField(blank=True, null=True)

    file = models.FileField(upload_to='invoices/')
    extracted_text = models.TextField(blank=True, null=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_invoices"
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_invoices"
    )

    rejected_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name}"