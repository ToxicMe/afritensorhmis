from django.shortcuts import render, get_object_or_404, redirect
from doctor.models import DoctorNote
from .models import TestResult, TestResultEntry, Test
from registration.models import Visit
from django.utils import timezone
from accounts.models import CustomUser
from doctor.views import *
# Create your views here.


def all_tests_list(request):
    tests = Test.objects.prefetch_related('hospital_available').all()
    return render(request, 'laboratory/all_tests_list.html', {'tests': tests})




def submit_test_findings(request, note_id):
    note = get_object_or_404(DoctorNote, id=note_id)
    visit = note.visit
    patient = note.patient

    if request.method == 'POST':
        test_result = TestResult.objects.create(
            visit=visit,
            patient=patient,
            done_by=request.user
        )

        for test in note.tests.all():
            result_text = request.POST.get(f'finding_{test.id}', '')
            TestResultEntry.objects.create(
                test_result=test_result,
                test=test,
                result=result_text
            )

        # Optionally update the visit stage
        visit.stage = 'prescription'
        visit.save()

        return redirect(lab_visits_list)  # Adjust to wherever you want

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

    visits = Visit.objects.filter(
        stage='laboratory',
        hospital=user.hospital,
        doctor_notes__isnull=False  # Only visits that have doctor notes
    ).distinct().order_by('updated_on')

    return render(request, 'laboratory/laboratory_visits_list.html', {
        'visits': visits
    })