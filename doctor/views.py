from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from accounts.models import CustomUser
from doctor.models import DoctorNote, PrescriptionNote
from laboratory.models import Test, TestResult, TestResultEntry
from billing.models import Bill  
from django.db import transaction


# Create your views here.
# Create your views here.
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
        stage='doctor',
        hospital=user.hospital
    ).order_by('updated_on')

    return render(request, 'doctor/doctor_visits_list.html', {
        'visits': visits
    })