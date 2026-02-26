from django.db import models
from django.conf import settings
from accounts.models import Company


class Expense(models.Model):

    CATEGORY_CHOICES = [
        ('Personal', 'Personal'),
        ('Business', 'Business'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
    ('pending', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('paid', 'Paid'),
]


    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)


    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    from django.conf import settings

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses"
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_expenses"
    )

    rejected_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title