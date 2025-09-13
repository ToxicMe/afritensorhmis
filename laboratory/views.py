from django.shortcuts import render, get_object_or_404, redirect
from doctor.models import DoctorNote
from .models import TestResult, TestResultEntry, Test
from registration.models import Visit
from django.utils import timezone
from accounts.models import CustomUser
from doctor.views import *
from django.contrib import messages
from datetime import date
from django.db.models import Q

# Create your views here.


def all_tests_list(request):
    tests = Test.objects.prefetch_related('hospital_available').all()
    return render(request, 'laboratory/all_tests_list.html', {'tests': tests})




def submit_test_findings(request, note_id):
    note = get_object_or_404(DoctorNote, id=note_id)
    visit = note.visit
    patient = note.patient

    if request.method == 'POST':
        try:
            # Create the main test result record
            test_result = TestResult.objects.create(
                visit=visit,
                patient=patient,
                done_by=request.user
            )

            # Loop through attached tests
            for test in note.tests.all():
                result_text = request.POST.get(f'finding_{test.id}', '')
                TestResultEntry.objects.create(
                    test_result=test_result,
                    test=test,
                    result=result_text
                )

            # Update visit stage
            visit.stage = 'prescription'
            visit.save()

            messages.success(request, "✅ Test findings saved successfully.")
            return redirect('laboratory_visits_list')  # Use the correct named URL

        except Exception as e:
            messages.error(request, f"❌ Error saving test findings: {e}")
            return redirect('view_doctor_note', visit_id=visit.id)

    # If not POST, just go back
    return redirect('view_doctor_note', visit_id=visit.id)



def laboratory(request):
    return render(request, 'laboratory/dashboard.html')

def lab_visits_list(request):
    user = request.user

    if not hasattr(user, 'hospital') or not user.hospital:
        return render(request, 'laboratory/laboratory_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits_qs = Visit.objects.filter(
        stage='laboratory',
        hospital=user.hospital,
        doctor_notes__isnull=False  # Only visits that have doctor notes
    ).distinct().order_by('updated_on')

    # Prepare structured data
    visits = []
    for v in visits_qs:
        visits.append({
            "id": v.id,
            "code": v.tracking_code,
            "name": v.patient.get_full_name() if hasattr(v.patient, "get_full_name") else v.patient.username,
            "age": v.patient.age if hasattr(v.patient, "age") else None,
            "gender": v.patient.gender if hasattr(v.patient, "gender") else "N/A",
            "hospital": v.hospital.name,
            "date": v.date_time,
        })

    return render(request, 'laboratory/laboratory_visits_list.html', {
        'visits': visits
    })
