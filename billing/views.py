from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Max
from django.contrib import messages
from django.db import transaction
from accounts.models import CustomUser
from .models import *
from django.db.models import Sum, Max, Q, Value, CharField, F, fields, ExpressionWrapper
from registration.models import Visit
from .payment_processors.mpesa import mpesa_pay  # your helper
from django.db.models import Sum
from django.http import HttpResponse
from billing.utils import create_payment_receipt
from collections import defaultdict
from datetime import date
from django.db.models.functions import Concat, Cast
from django.utils.timezone import localdate, now
from django.db.models.functions import Coalesce



def view_patient_bill(request, patient_id):
    # Ensure it's really a patient
    patient = get_object_or_404(CustomUser, id=patient_id, account_type="patient")

    # Get latest active visit for this patient
    visit = Visit.objects.filter(patient=patient).order_by("-date_time").first()
    if not visit:
        return render(request, "billing/bill_receipt.html", {
            "patient": patient,
            "visit": None,
            "bills": [],
            "total_amount": 0,
            "error": "No visits found for this patient."
        })

    # Fetch bills created on the same DATE as the visit datetime
    all_bills = Bill.objects.filter(
        patient=patient,
        created_at__date=localdate(visit.date_time)
    )

    # Pending bills total
    pending_total = (
        all_bills.filter(status="pending").aggregate(Sum("amount"))["amount__sum"] or 0
    )

    # ✅ Calculate age
    patient_age = None
    if patient.date_of_birth:
        today = date.today()
        patient_age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

    context = {
        "visit": visit,
        "patient": patient,
        "patient_age": patient_age if patient_age is not None else "N/A",
        "patient_gender": patient.gender.capitalize() if patient.gender else "N/A",
        "bills": all_bills,
        "total_amount": pending_total,
    }
    return render(request, "billing/bill_receipt.html", context)


def all_payment_receipts(request):
    receipts = PaymentReceipt.objects.select_related("patient", "visit", "created_by").order_by("-date_created")

    # Add total paid to each receipt
    for receipt in receipts:
        total_paid = receipt.visit.bills.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        receipt.total_paid = total_paid

    # Unique cashier names
    cashiers = sorted(set([r.created_by.get_full_name() for r in receipts if r.created_by]))

    return render(request, 'billing/receipt_list.html', {
        "receipts": receipts,
        "cashiers": cashiers
    })

def view_payment_receipt(request, receipt_id):
    receipt = get_object_or_404(PaymentReceipt, receipt_id=receipt_id)
    visit = receipt.visit
    patient = receipt.patient
    bills = Bill.objects.filter(visit=visit, status='paid')

    total_amount = bills.aggregate(total=Sum('amount'))['total'] or 0

    # ✅ Calculate age
    patient_age = None
    if patient.date_of_birth:
        today = date.today()
        patient_age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

    context = {
        'receipt': receipt,
        'visit': visit,
        'patient': patient,
        'patient_age': patient_age if patient_age is not None else "N/A",
        'patient_gender': patient.gender.capitalize() if patient.gender else "N/A",
        'bills': bills,
        'total_amount': total_amount,
    }

    return render(request, 'billing/receipt_detail.html', context)




def all_bills(request):
    today = date.today()
    results = []

    # Group bills by visit manually
    visits = Bill.objects.values_list("visit", flat=True).distinct()

    for visit_id in visits:
        bills = Bill.objects.filter(visit_id=visit_id).select_related("patient", "visit")

        if not bills.exists():
            continue

        total_amount = bills.aggregate(Sum("amount"))["amount__sum"]
        latest_bill = bills.latest("date")  # get most recent bill

        patient = latest_bill.patient
        if patient:
            patient_name = patient.patient_name or "Unknown"
            patient_gender = patient.gender or "Unknown"

            if patient.date_of_birth:
                patient_age = (
                    today.year - patient.date_of_birth.year
                    - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
                )
            else:
                patient_age = "N/A"
        else:
            patient_name = "Unknown"
            patient_gender = "Unknown"
            patient_age = "N/A"

        results.append({
            "visit": visit_id,
            "total_amount": total_amount,
            "latest_date": latest_bill.date,
            "tracking_code": latest_bill.visit.tracking_code if latest_bill.visit else None,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "status": latest_bill.status,
            "transaction_id": latest_bill.transaction_id,
        })

    # sort by latest date (descending)
    results = sorted(results, key=lambda x: x["latest_date"], reverse=True)

    return render(request, "billing/unpaid_bills_list.html", {"grouped_bills": results})




def view_bill(request, transaction_id):
    # Get the bill by transaction_id to extract the visit
    main_bill = get_object_or_404(Bill, transaction_id=transaction_id)
    visit = main_bill.visit
    patient = main_bill.patient

    # Fetch all bills for the same visit
    all_bills = Bill.objects.filter(visit=visit)

    # Filter only pending bills for the total
    pending_total = all_bills.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0

    # ✅ Calculate age
    patient_age = None
    if patient.date_of_birth:
        today = date.today()
        patient_age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

    context = {
        'visit': visit,
        'patient': patient,
        'patient_age': patient_age if patient_age is not None else "N/A",
        'patient_gender': patient.gender.capitalize() if patient.gender else "N/A",
        'bills': all_bills,
        'total_amount': pending_total,
    }
    return render(request, 'billing/bill_receipt.html', context)




def billing(request):
    return render(request, 'billing/dashboard.html')



def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))



def unpaid_bills_list(request):
    bills_by_visit = (
        Bill.objects.filter(status='pending')
        .exclude(description__icontains='pharmacy')
        .values('visit')
        .annotate(
            total_amount=Sum('amount'),
            latest_date=Max('date'),
            tracking_code=Max('visit__tracking_code'),
            patient_id=Max('patient__id'),
            patient_name=Max('patient__patient_name'),
            patient_gender=F('visit__patient__gender'),
            patient_dob=Max('patient__date_of_birth'),
            description=Max('description'),
            status=Max('status'),
            transaction_id=Max('transaction_id')
        )
        .order_by('-latest_date')
    )

    # Calculate age server-side
    for bill in bills_by_visit:
        dob = bill.get('patient_dob')
        if dob:
            today = date.today()
            bill['patient_age'] = (
                today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            )
        else:
            bill['patient_age'] = None

    return render(request, 'billing/unpaid_bills_list.html', {'grouped_bills': bills_by_visit})



@transaction.atomic
def mark_bills_paid(request, tracking_code):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("home")

    payment_method = request.POST.get("payment_method", "cash")
    visit = get_object_or_404(Visit, tracking_code=tracking_code)
    pending_bills = Bill.objects.select_for_update().filter(visit=visit, status='pending')

    if not pending_bills.exists():
        messages.warning(request, "There are no pending bills to update.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    total_amount = pending_bills.aggregate(total=Sum('amount'))['total'] or 1

    # Handle Mpesa payment
    if payment_method == "mpesa":
        try:
            response = mpesa_pay(visit.patient.phone_number, total_amount, visit.patient.get_full_name())
            if response.response_code != '0':
                messages.error(request, "M-Pesa request failed. Please try again.")
                return redirect(request.META.get("HTTP_REFERER", "/"))
        except Exception as e:
            messages.error(request, f"M-Pesa Error: {str(e)}")
            return redirect(request.META.get("HTTP_REFERER", "/"))

    # Save the first bill for redirect
    first_bill = pending_bills.first()

    # Mark all bills as paid
    pending_bills.update(status='paid', payment_method=payment_method)

    # ✅ Create receipt using utility function
    receipt, error = create_payment_receipt(
        visit=visit,
        patient=visit.patient,
        amount = total_amount,
        payment_method=payment_method,
        created_by=request.user
    )

    if error:
        messages.error(request, f"Failed to create receipt: {error}")
    else:
        messages.success(request, f"Receipt {receipt.receipt_id} created.")

    # ✅ Update visit stage
    if visit.stage == "billing_note":
        visit.stage = "laboratory"
    elif visit.stage == "billing_prescription":
        visit.stage = "pharmacy"
    elif visit.stage == "billing_pharmacy":
        visit.stage = "discharged"
    else:
        visit.stage = "triage"

    visit.save()

    messages.success(request, f"All bills for Visit {tracking_code} marked as paid.")
    return redirect('view_bill', transaction_id=first_bill.transaction_id)