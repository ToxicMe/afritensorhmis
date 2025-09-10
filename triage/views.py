from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from .models import Triage
from django.utils import timezone
from datetime import date

# Create your views here.

def create_triage(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    patient = visit.patient
    today = date.today()

    # Try to get existing triage for this patient and visit
    triage = Triage.objects.filter(patient=patient, visit=visit).first()

    if request.method == 'POST':
        # Get form values
        bp_sys = request.POST.get('bp')
        bp_dia = request.POST.get('bp_dia')
        pr = request.POST.get('pr')
        spo2 = request.POST.get('spo2')
        rbs = request.POST.get('rbs')
        temperature = request.POST.get('temperature')
        height = request.POST.get('height')
        weight = request.POST.get('weight')

        # Calculate BMI server-side as backup
        bmi = None
        try:
            h_m = float(height) / 100 if height else None
            w_kg = float(weight) if weight else None
            if h_m and w_kg:
                bmi = round(w_kg / (h_m ** 2), 1)
        except ValueError:
            bmi = None

        if triage:
            # Update existing triage
            triage.bp_sys = bp_sys if bp_sys else None
            triage.bp_dia = bp_dia if bp_dia else None
            triage.pr = pr if pr else None
            triage.spo2 = spo2 if spo2 else None
            triage.rbs = rbs if rbs else None
            triage.temperature = temperature if temperature else None
            triage.height = height if height else None
            triage.weight = weight if weight else None
            triage.bmi = bmi
            triage.recorder_by = request.user
            triage.timestamp = timezone.now()
        else:
            # Create new triage
            triage = Triage(
                visit=visit,
                patient=patient,
                bp_sys=bp_sys if bp_sys else None,
                bp_dia=bp_dia if bp_dia else None,
                pr=pr if pr else None,
                spo2=spo2 if spo2 else None,
                rbs=rbs if rbs else None,
                temperature=temperature if temperature else None,
                height=height if height else None,
                weight=weight if weight else None,
                bmi=bmi,
                recorder_by=request.user,
                timestamp=timezone.now(),
            )
        triage.save()

        # Update visit stage to 'doctor'
        visit.stage = 'doctor'
        visit.save()

        return redirect('triage_visits_list')

    # Pre-fill form data for GET request if triage exists
    form_data = {}
    if triage:
        form_data = {
            'bp': triage.bp_sys,
            'bp_dia': triage.bp_dia,
            'pr': triage.pr,
            'spo2': triage.spo2,
            'rbs': triage.rbs,
            'temperature': triage.temperature,
            'height': triage.height,
            'weight': triage.weight,
            'bmi': triage.bmi,
        }

    # Calculate exact age
    age = None
    if patient.date_of_birth:
        dob = patient.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    return render(request, 'triage/create_triage.html', {
        'visit': visit,
        'patient': patient,
        'age': age,
        'form_data': form_data,
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
    ).select_related("patient") \
     .order_by('updated_on')  # oldest first

    today = date.today()
    for visit in visits:
        dob = visit.patient.date_of_birth
        if dob:
            visit.patient_age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
        else:
            visit.patient_age = "N/A"

        visit.patient_gender = visit.patient.gender.capitalize() if visit.patient.gender else "N/A"

    return render(request, 'triage/triage_visits_list.html', {
        'visits': visits
    })