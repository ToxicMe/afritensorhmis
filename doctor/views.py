from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from accounts.models import CustomUser
from doctor.models import DoctorNote, PrescriptionNote
from laboratory.models import Test, TestResult, TestResultEntry
from billing.models import Bill  
from django.db import transaction
from django.db.models import Q, Sum, Max
from billing.utils import create_patient_bill
from django.contrib import messages


# Create your views here.
# Create your views here.
def doctor_unpaid_bills_list(request):
    bills_by_visit = (
        Bill.objects
        .filter(
            status='pending',
            visit__type__in=['minor_surgery', 'outpatient_consultation']
        )
        .exclude(description__icontains='pharmacy')  # still exclude pharmacy-related
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
            transaction_id=Max('transaction_id')
        )
        .order_by('-latest_date')
    )

    return render(request, 'billing/unpaid_bills_list.html', {'grouped_bills': bills_by_visit})


def add_bill_from_note(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    patient = visit.patient

    if request.method == "POST":
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        reason = request.POST.get("reason", "").strip()

        bill, error = create_patient_bill(
            visit=visit,
            patient=patient,
            description=description,
            amount=amount,
            discount_reason=reason if reason else None
        )

        if bill:
            messages.success(request, "Bill added successfully.")
        else:
            messages.error(request, f"Failed to add bill: {error}")

    return redirect("add_doctor_note", visit_id=visit_id)

def doctor(request):
    return render(request, 'doctor/dashboard.html')

@transaction.atomic
def add_doctor_note(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    patient = visit.patient
    tests = Test.objects.filter(hospital_available=visit.hospital)

    if request.method == 'POST':
        doctor_notes = request.POST.get('doctor_notes')
        selected_test_ids = request.POST.getlist('tests')

        if doctor_notes:
            note = DoctorNote.objects.create(
                visit=visit,
                patient=patient,
                doctor_notes=doctor_notes,
                done_by=request.user
            )

            if selected_test_ids:
                selected_tests = Test.objects.filter(id__in=selected_test_ids)
                note.tests.set(selected_tests)

                # ✅ Create a Bill for each selected test
                for test in selected_tests:
                    Bill.objects.create(
                        visit=visit,
                        patient=patient,
                        description=f"Test: {test.name}",
                        amount=test.price,
                        status='pending'  # Default to pending
                    )

            # ✅ Update visit stage
            visit.stage = 'billing_note'
            visit.save()

            return redirect('doctor_visits_list')  # Replace with correct name
        else:
            error = "Doctor notes are required."
            return render(request, 'doctor/doctor_note.html', {
                'visit': visit,
                'patient': patient,
                'tests': tests,
                'error': error
            })

    return render(request, 'doctor/doctor_note.html', {
        'visit': visit,
        'patient': patient,
        'tests': tests
    })




def prescription_visits_list(request):
    user = request.user

    if not user.hospital:
        return render(request, 'doctor/prescription_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits = Visit.objects.filter(
        stage='prescription',
        hospital=user.hospital
    ).order_by('-date_time').select_related('patient', 'hospital')

    return render(request, 'doctor/prescription_visits_list.html', {
        'visits': visits
    })

def view_test_results_for_prescription(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)
    test_results = visit.test_results.prefetch_related('entries__test')
    return render(request, 'doctor/view_test_results.html', {
        'visit': visit,
        'test_results': test_results
    })



def save_prescription_note(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)

    if request.method == 'POST':
        note = request.POST.get('doctor_prescription')
        if note:
            PrescriptionNote.objects.create(
                visit=visit,
                patient=visit.patient,
                doctor_prescription=note,
                done_by=request.user
            )
            visit.stage = 'pharmacy'  # Optionally update stage
            visit.save()
            return redirect(prescription_visits_list)  # Or wherever you want to go after
        else:
            return render(request, 'doctor/view_test_results.html', {
                'visit': visit,
                'test_results': visit.test_results.all(),
                'error': 'Prescription note is required.'
            })


def view_doctor_note(request, visit_id):
    note = get_object_or_404(DoctorNote, visit_id=visit_id)
    tests = note.tests.all()

    return render(request, 'laboratory/view_doctor_note.html', {
        'note': note,
        'tests': tests
    })


def doctor_visits_list(request):
    user = request.user

    if not user.hospital:
        return render(request, 'doctor/doctor_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits = Visit.objects.filter(
        Q(stage='doctor') | Q(stage='minor_surgery') | Q(stage='consultation'),
        hospital=user.hospital
    ).order_by('updated_on')  # oldest first

    return render(request, 'doctor/doctor_visits_list.html', {
        'visits': visits
    })