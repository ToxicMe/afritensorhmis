import string
import random
from django.db import models
from django.utils import timezone

from registration.models import Visit
from accounts.models import CustomUser


def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


class Bill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'Mpesa'),
        ('card', 'Card'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]

    transaction_id = models.CharField(max_length=10, unique=True, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='bills')
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bills')
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            while True:
                new_id = generate_transaction_id()
                if not Bill.objects.filter(transaction_id=new_id).exists():
                    self.transaction_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill {self.transaction_id} for {self.patient.get_full_name() or self.patient.username}"



class PaymentReceipt(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'Mpesa'),
        ('card', 'Card'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='payment_receipts')
    receipt_id = models.CharField(max_length=12, unique=True, editable=False)
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_receipts')
    date_created = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='receipts_created')

    def save(self, *args, **kwargs):
        if not self.receipt_id:
            self.receipt_id = generate_transaction_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_id} for {self.patient.get_full_name() or self.patient.username}"