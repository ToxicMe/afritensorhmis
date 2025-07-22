# billing/utils.py

from decimal import Decimal
from django.utils import timezone
from .models import Bill


def create_patient_bill(
    patient,
    description,
    amount,
    visit=None,
    status='pending',
    payment_method=None,
    discounted=False,
    custom_amount=None,
    discount_reason=None
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
            discount_reason=discount_reason
        )
        return bill, None  # Success
    except Exception as e:
        return None, str(e)
