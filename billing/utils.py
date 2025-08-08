# billing/utils.py

from decimal import Decimal
from django.utils import timezone
from .models import Bill
from .models import PaymentReceipt
from django.utils import timezone
from django.core.exceptions import ValidationError
from registration.models import Visit
from accounts.models import CustomUser

def create_payment_receipt(visit, patient, amount, payment_method, created_by=None):
    """
    Creates a PaymentReceipt object and saves it to the database.

    Args:
        visit (Visit): The visit associated with the payment.
        patient (CustomUser): The patient making the payment.
        payment_method (str): One of the allowed payment methods.
        created_by (CustomUser): The user creating the receipt (optional).

    Returns:
        tuple: (receipt, error)
            - receipt: The created PaymentReceipt instance or None
            - error: Error message if failed, else None
    """
    if not visit or not patient:
        return None, "Visit and patient are required."

    if payment_method not in dict(PaymentReceipt.PAYMENT_METHOD_CHOICES):
        return None, "Invalid payment method."

    # Set status based on payment method
    status = 'pending' if payment_method == 'insurance' else 'paid'

    try:
        receipt = PaymentReceipt.objects.create(
            visit=visit,
            patient=patient,
            amount = amount,
            payment_method=payment_method,
            created_by=created_by,
            status=status,
            date_created=timezone.now()
        )
        return receipt, None
    except Exception as e:
        return None, str(e)









def create_patient_bill(
    patient,
    description,
    amount,
    visit=None,
    status='pending',
    payment_method=None,
    discounted=False,
    custom_amount=None,
    discount_reason=None,
    created_by=None
):
    """
    Create and save a Bill instance with reusable defaults.
    """
    try:
        bill = Bill.objects.create(
            visit=visit,
            patient=patient,
            description=description,
            amount=Decimal(amount),
            date=timezone.now(),
            status=status,
            payment_method=payment_method,
            discounted=discounted,
            custom_amount=Decimal(custom_amount) if custom_amount else None,
            discount_reason=discount_reason,
            created_by=created_by
        )
        return bill, None  # Success
    except Exception as e:
        return None, str(e)
