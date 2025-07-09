
from django.db import models
from django.contrib.auth.models import User  # Or your custom user model
from django.contrib.auth import get_user_model




class Requisition(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='requisitions')
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.EmailField()
    date_of_request = models.DateField()
    is_urgent = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    done_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='done_by_requisitions')

    def __str__(self):
        return f"Requisition by {self.user} on {self.date_of_request}"




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
