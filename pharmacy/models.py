from django.db import models
from django.utils import timezone
import uuid
from django.utils.text import slugify
from finance.models import Supplier
from accounts.models import CustomUser
from companies.models import *
from registration.models import *
from doctor.models import PrescriptionNote
from django.db import transaction

class Pharmacy(models.Model):
    id = models.AutoField(primary_key=True)
    company_name =models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='pharmacies_companies')
    hospital_name = models.ForeignKey('hospital.Hospital', on_delete=models.CASCADE, related_name='pharmacies')
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacies_added')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.company_name} at {self.hospital_name}"

class Consignment(models.Model):
    id = models.AutoField(primary_key=True)
    consignment_id = models.CharField(max_length=100, unique=True, default=None, null=True, blank=True)
    supplier = models.ForeignKey('finance.Supplier', on_delete=models.CASCADE, related_name='consignments', default=None, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ], default='pending')

    consignment_products = models.ManyToManyField('Product', related_name='consignments_products', blank=True)
    quantity = models.PositiveIntegerField(default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    is_disputed = models.BooleanField(default=False)
    is_invoiced = models.BooleanField(default=False)
    is_billed = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)
    is_received = models.BooleanField(default=False)
    is_returned_to_supplier = models.BooleanField(default=False)
    pharmacy = models.ForeignKey('pharmacy.Pharmacy', on_delete=models.CASCADE, related_name='consignments')
    entry_date = models.DateTimeField(default=timezone.now)
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='consignments_added')


    def generate_consignment_id(self):
        return f"CONS-{uuid.uuid4().hex[:10].upper()}"

    def save(self, *args, **kwargs):
        if not self.consignment_id:
            self.consignment_id = self.generate_consignment_id()
        super().save(*args, **kwargs)

    def total_value(self):
        return sum(product.acquiring_price * product.quantity for product in self.products.all())

    def __str__(self):
        return f"Consignment #{self.id} for {self.pharmacy.company_name}"

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    consignment = models.ForeignKey('pharmacy.Consignment', on_delete=models.CASCADE, related_name='products')
    sku_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    acquiring_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)  
    quantity = models.PositiveIntegerField()
    expiry_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='products_added')
    created_at = models.DateTimeField(default=timezone.now)


    def save(self, *args, **kwargs):
            if not self.sku_id:
                abbrev = slugify(self.name)[:4].upper()
                random_id = uuid.uuid4().hex[:6].upper()
                self.sku_id = f"SKU-{self.consignment.id}-{abbrev}-{random_id}"
            super().save(*args, **kwargs)

    def __str__(self):
            return f"{self.name} ({self.consignment})"



class Sale(models.Model):
    # Optional patient & visit for walk-in sales
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sales', null=True, blank=True)
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='sales', null=True, blank=True)

    # Add walk-in fields
    walk_in_name = models.CharField(max_length=255, blank=True, null=True)
    walk_in_phone = models.CharField(max_length=20, blank=True, null=True)
    walk_in_prescription = models.TextField(blank=True, null=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('mpesa', 'Mpesa'),
        ('card', 'Card'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ])
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.visit:
            return f"{self.visit}) - {self.amount} ({self.status})"
        elif self.walk_in_name:
            return f"Walk-in: {self.walk_in_name} - {self.amount} ({self.status})"
        else:
            return f"Sale #{self.id} - {self.amount} ({self.status})"


class SaleItem(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    description = models.TextField(blank=True, null=True)

    def subtotal(self):
        return self.quantity * self.price