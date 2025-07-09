from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from .models import Triage
from django.utils import timezone
# Create your views here.

def create_triage(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    patient = visit.patient

    if request.method == 'POST':
        triage = Triage(
            visit=visit,
            patient=patient,
            recorder_by=request.user,
            timestamp=timezone.now(),
            bp=request.POST.get('bp'),
            bp_dia=request.POST.get('bp_dia'),
            pr=request.POST.get('pr'),
            spo2=request.POST.get('spo2'),
            rbs=request.POST.get('rbs'),
            temperature=request.POST.get('temperature'),
            height=request.POST.get('height'),
            weight=request.POST.get('weight'),
            bmi=request.POST.get('bmi'),
            body_fat=request.POST.get('body_fat'),
            muscle_mass=request.POST.get('muscle_mass'),
            bone_mass=request.POST.get('bone_mass'),
            metabo_age=request.POST.get('metabo_age'),
            calories=request.POST.get('calories'),
            visce=request.POST.get('visce'),
        )
        triage.save()

        # Update visit stage to 'note'
        visit.stage = 'doctor'
        visit.save()

        return redirect('triage_visits_list')

    return render(request, 'triage/create_triage.html', {
        'visit': visit,
        'patient': patient
    })



def triage(request):
    return render(request, 'triage/dashboard.html')

def triage_visits_list(request):
    user = request.user

    if not user.hospital:
        return render(request, 'triage/triage_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits = Visit.objects.filter(
        stage='triage',
        hospital=user.hospital
    ).order_by('updated_on')

    return render(request, 'triage/triage_visits_list.html', {
        'visits': visits
    })