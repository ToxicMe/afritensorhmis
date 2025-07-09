from django.db import models
from django.utils import timezone
import uuid
from django.utils.text import slugify


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
    pharmacy = models.ForeignKey('pharmacy.Pharmacy', on_delete=models.CASCADE, related_name='consignments')
    entry_date = models.DateTimeField(default=timezone.now)
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='consignments_added')

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
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sales')
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='sales')
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
        return f"{self.visit}) - {self.amount} ({self.status})"

class SaleItem(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
            return f"{self.sale}) - {self.product} - ({self.quantity}) - {self.price})"