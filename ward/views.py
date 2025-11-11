from django.shortcuts import render
from registration.models import Visit
from datetime import date

# Create your views here.
def ward_dashboard(request):
    return render(request, 'wards/dashboard.html')


def ward_visits_list(request):
    user = request.user

    if not user.hospital:
        return render(request, 'wards/ward_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits = Visit.objects.filter(
        stage='admitted',
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

    return render(request, 'wards/ward_visits_list.html', {
        'visits': visits
    })