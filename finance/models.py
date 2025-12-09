
from django.db import models
from django.contrib.auth.models import User  # Or your custom user model
from django.contrib.auth import get_user_model
import uuid
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings
from hospital.models import Hospital  # adjust if hospital model path differs

class CashAccount(models.Model):
    

    name = models.CharField(max_length=100, unique=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='account_hospital', default=1)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=500, unique=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    financial_statement_category = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default='KES')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    done_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='account_added_by')


    def __str__(self):
        return f"{self.name} ({self.currency})"

   



class PettyCashEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('debit', 'Debit'),   # cash in
        ('credit', 'Credit'), # cash out
    ]

    # Ledger accounts
    debit_ledger_account = models.CharField(max_length=300)
    credit_ledger_account = models.CharField(max_length=300)

    # Dates
    posting_date = models.DateTimeField(auto_now_add=True)
    document_date = models.DateField(default=now)

    # Document details
    document_type = models.CharField(max_length=80, blank=True, null=True)
    document_no = models.CharField(max_length=80, blank=True, null=True)
    external_document_no = models.CharField(max_length=80, blank=True, null=True)

    # Account info
    acc_type = models.CharField(max_length=80, blank=True, null=True)
    acc_no = models.CharField(max_length=80, blank=True, null=True)
    balance_acc_type = models.CharField(max_length=150)
    balance_acc_no = models.CharField(max_length=150)

    # Description
    description = models.TextField(max_length=500, blank=True, null=True)

    # Amounts
    debit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # Additional info
    branch_code = models.CharField(max_length=150, blank=True, null=True)
    department_code = models.CharField(max_length=150, blank=True, null=True)
    line_no = models.CharField(max_length=150, blank=True, null=True)

    # User
    done_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='petty_added_by'
    )

    # Entry type
    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPE_CHOICES,
        default='debit'
    )

    class Meta:
        ordering = ['-posting_date']

    def __str__(self):
        return f"{self.document_no} - {self.acc_type} - {self.debit_amount} / {self.credit_amount}"
    

class LedgerEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    date = models.DateField()
    account_number = models.CharField(max_length=20)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entry_type = models.CharField(max_length=6, choices=ENTRY_TYPE_CHOICES)
    text = models.TextField(blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    entry_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_added_by')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.account_number} - {self.entry_type.upper()} - {self.amount}"

    def debit_amount(self):
        return self.amount if self.entry_type == 'debit' else None

    def credit_amount(self):
        return self.amount if self.entry_type == 'credit' else None

class FixedAsset(models.Model):
    asset_id = models.CharField(max_length=100, unique=True)
    asset_class = models.CharField(max_length=100)
    
    purchase_date = models.DateField()
    disposal_date = models.DateField(null=True, blank=True)
    
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='fixed_assets')

    description = models.TextField(blank=True, null=True)

    cost = models.DecimalField(max_digits=12, decimal_places=2)
    additions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disposal_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    total_asset = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    opening_depreciation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation_for_year = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation_on_disposal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    net_book_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    done_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_added')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_asset = (self.cost or 0) + (self.additions or 0)
        self.net_book_value = self.total_asset - (
            (self.opening_depreciation or 0) +
            (self.depreciation_for_year or 0) +
            (self.depreciation_on_disposal or 0)
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_id} - {self.asset_class}"


class Requisition(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='requisitions')
    requisition_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.EmailField()
    date_of_request = models.DateField()
    is_urgent = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], default='pending')
    date_of_approval = models.DateField(blank=True, null=True)
    date_of_completion = models.DateField(blank=True, null=True)
    date_of_rejection = models.DateField(blank=True, null=True)
    reason_for_rejection = models.TextField(blank=True, null=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    done_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='done_by_requisitions')

    def save(self, *args, **kwargs):
        if not self.requisition_id:
            today = now().date()
            date_str = today.strftime('%Y%m%d')
            count = Requisition.objects.filter(date_of_request=today).count() + 1
            self.requisition_id = f"REQ-{date_str}{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.requisition_id} by {self.user}"




class RequisitionItem(models.Model):
    requisition = models.ForeignKey(Requisition, related_name="items", on_delete=models.CASCADE)
    item_description = models.CharField(max_length=200)
    unit = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.item_description


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    tax_id = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.CharField(max_length=255, blank=True, null=True)

    website = models.URLField(blank=True, null=True)
    status = models.BooleanField(default=True)

    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='suppliers_added')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='purchase_orders')
    requisition = models.ForeignKey('Requisition', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ], default='pending')

    payment_terms = models.CharField(max_length=255, blank=True, null=True)
    delivery_location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='purchase_orders_created')
    approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders_approved')
    approved_at = models.DateTimeField(blank=True, null=True)

    import uuid

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = f"PO-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PO-{self.po_number}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item_description = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.item_description
