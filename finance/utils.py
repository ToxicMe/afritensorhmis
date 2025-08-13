from django.db.models import Sum, Case, When, F, DecimalField, Q
from .models import *
from billing.models import * 


#ALL BILLS
def get_total_all_bills():
    """
    Returns the total of all bills in the system,
    using custom_amount if present, otherwise amount.
    """
    total = Bill.objects.aggregate(
        total=Sum(
            Case(
                When(custom_amount__isnull=False, then=F('custom_amount')),
                default=F('amount'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    return total

#PHARMACY BILLS
def get_total_pharmacy_bills():
    """Return the total pharmacy bill value using custom_amount if available."""
    return Bill.objects.filter(
        Q(visit__stage='billing_pharmacy') | Q(visit__isnull=True)
    ).aggregate(
        total=Sum(
            Case(
                When(custom_amount__isnull=False, then=F('custom_amount')),
                default=F('amount'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0


#PETTY CASH ENTRIES
def get_total_petty_cash_debit():
    return PettyCashEntry.objects.filter(entry_type='debit').aggregate(
        total=Sum('amount')
    )['total'] or 0
    

#FIXED ASSETS
def get_total_leasehold_value():
    return FixedAsset.objects.filter(
        asset_class__iexact="LEASEHOLD IMPROVEMENTS"
    ).aggregate(
        total=Sum('net_book_value')
    )['total'] or 0

#COMPUTERS
def get_total_computers_value():
    return FixedAsset.objects.filter(
        asset_class__iexact="COMPUTERS"
    ).aggregate(
        total=Sum('net_book_value')
    )['total'] or 0

#NET BOOK VALUE
def get_total_net_book_value():
    return FixedAsset.objects.aggregate(
        total=Sum('net_book_value')
    )['total'] or 0

#INSURANCE BILLS
def get_total_insurance_bills():
    return Bill.objects.filter(
        status='paid',
        payment_method='insurance'
    ).aggregate(
        total=Sum(
            Case(
                When(custom_amount__isnull=False, then=F('custom_amount')),
                default=F('amount'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

#CONSULTATION

def get_total_consultation_bills():
    """
    Returns the total of all consultation bills, 
    using custom_amount if present, otherwise amount.
    """
    total = Bill.objects.filter(
        description__icontains='Consultation'  # adjust filter to your exact field/value
    ).aggregate(
        total=Sum(
            Case(
                When(custom_amount__isnull=False, then=F('custom_amount')),
                default=F('amount'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0


#TESTS BILLS
def get_total_test_bills():
    """
    Returns the total of all test bills 
    (description starting with 'Test:'), 
    using custom_amount if present, otherwise amount.
    """
    total = Bill.objects.filter(
        description__istartswith='Test:'  # matches "Test: ..." regardless of case
    ).aggregate(
        total=Sum(
            Case(
                When(custom_amount__isnull=False, then=F('custom_amount')),
                default=F('amount'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    return total