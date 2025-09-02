from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from accounts.models import CustomUser
from doctor.models import DoctorNote, PrescriptionNote, ICD10Entry
from laboratory.models import Test, TestResult, TestResultEntry
from billing.models import Bill  
from django.db import transaction
from django.db.models import Q, Sum, Max
from billing.utils import create_patient_bill
from django.contrib import messages
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from doctor.models import ICD10Entry
from django.core.serializers.json import DjangoJSONEncoder
# Create your views here.


def get_icd10_children(request, parent_id):
    children = ICD10Entry.objects.filter(parent_id=parent_id).values('id', 'code', 'label', 'kind')
    return JsonResponse(list(children), safe=False)


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

def build_icd_hierarchy(entries):
    """Build a tree structure of ICD-10 entries for frontend dynamic dropdowns."""
    # Map all entries by ID
    entry_dict = {
        e.id: {
            'id': e.id,
            'code': e.code,
            'label': e.label,
            'kind': e.kind,
            'parent_id': e.parent_id,
            'children': []
        }
        for e in entries
    }

    # Build hierarchy by linking children to parents
    root = []
    for e in entry_dict.values():
        if e['parent_id']:
            parent = entry_dict.get(e['parent_id'])
            if parent:
                parent['children'].append(e)
        else:
            root.append(e)
    return root

@csrf_exempt
@transaction.atomic
def add_doctor_note(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    patient = visit.patient
    tests = Test.objects.filter(hospital_available=visit.hospital)

    # Fetch ICD-10 entries
    icd_entries = ICD10Entry.objects.all()  # Consider AJAX/pagination for large datasets
    icd10_hierarchy = build_icd_hierarchy(icd_entries)
    icd10_json = json.dumps(icd10_hierarchy, cls=DjangoJSONEncoder)

    error = None

    if request.method == 'POST':
        doctor_notes_text = request.POST.get('doctor_notes', '').strip()
        selected_test_ids = [int(i) for i in request.POST.getlist('tests') if i.isdigit()]
        selected_icd10_ids = [int(i) for i in request.POST.getlist('icd10_codes') if i.isdigit()]

        if not doctor_notes_text:
            error = "Doctor notes are required."
        else:
            # Create DoctorNote
            note = DoctorNote.objects.create(
                visit=visit,
                patient=patient,
                doctor_notes=doctor_notes_text,
                done_by=request.user
            )

            # Attach selected tests and create bills
            if selected_test_ids:
                selected_tests = Test.objects.filter(id__in=selected_test_ids)
                note.tests.set(selected_tests)
                for test in selected_tests:
                    Bill.objects.create(
                        visit=visit,
                        patient=patient,
                        description=f"Test: {test.name}",
                        amount=test.price,
                        status='pending'
                    )

            # Attach selected ICD-10 codes (multiple)
            if selected_icd10_ids:
                selected_icd_entries = ICD10Entry.objects.filter(id__in=selected_icd10_ids)
                note.icd10_codes.set(selected_icd_entries)

            # Update visit stage
            visit.stage = 'billing_note'
            visit.save()

            return redirect('doctor_visits_list')  # Adjust to your URL name

    return render(request, 'doctor/doctor_note.html', {
        'visit': visit,
        'patient': patient,
        'tests': tests,
        'icd10_codes': icd10_json,  # JSON for template
        'error': error
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