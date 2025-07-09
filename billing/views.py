from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Max
from django.contrib import messages
from django.db import transaction
from accounts.models import CustomUser
from .models import *
from registration.models import Visit



# Create your views here.



def view_bill(request, transaction_id):
    # Get the bill by transaction_id to extract the visit
    main_bill = get_object_or_404(Bill, transaction_id=transaction_id)
    visit = main_bill.visit

    # Fetch all bills for the same visit
    all_bills = Bill.objects.filter(visit=visit)

    # Filter only pending bills for the total
    pending_total = all_bills.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'visit': visit,
        'patient': main_bill.patient,
        'bills': all_bills,
        'total_amount': pending_total,
    }
    return render(request, 'billing/bill_receipt.html', context)



def billing(request):
    return render(request, 'billing/dashboard.html')


def unpaid_bills_list(request):
    # Group by visit and aggregate total amount and latest status
    bills_by_visit = (
        Bill.objects.filter(status='pending')
        .values('visit')
        .annotate(
            total_amount=Sum('amount'),
            latest_date=Max('date'),
            tracking_code=Max('visit__tracking_code'),
            patient_id=Max('patient__id'),
            patient_name=Max('patient__first_name'),
            patient_username=Max('patient__username'),
            description=Max('description'),
            status=Max('status'),
            transaction_id=Max('transaction_id')  # To link to receipt
        )
        .order_by('-latest_date')
    )
    return render(request, 'billing/unpaid_bills_list.html', {'grouped_bills': bills_by_visit})

@transaction.atomic
def mark_bills_paid(request, tracking_code):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "cash")

        visit = get_object_or_404(Visit, tracking_code=tracking_code)
        pending_bills = Bill.objects.select_for_update().filter(visit=visit, status='pending')

        if not pending_bills.exists():
            messages.warning(request, "There are no pending bills to update.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        # Mark all pending bills as paid
        pending_bills.update(status='paid', payment_method=payment_method)

        # Create a PaymentReceipt
        PaymentReceipt.objects.create(
            visit=visit,
            patient=visit.patient,
            payment_method=payment_method,
            created_by=request.user
        )

        messages.success(request, f"All bills for Visit {tracking_code} marked as paid.")
        return redirect('view_bill', transaction_id=pending_bills.first().transaction_id)

    messages.error(request, "Invalid request method.")
    return redirect("home")