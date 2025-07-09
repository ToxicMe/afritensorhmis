from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import CustomUser
from hospital.models import Hospital
from billing.models import Bill
from django.utils import timezone
from .models import Visit
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from billing.bills_processor import create_bill

# Create your views here.
def view_patient_visits(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id)
    visits = Visit.objects.filter(patient=patient).order_by('-date_time')
    return render(request, 'registration/patient_visits.html', {'patient': patient, 'visits': visits})


def create_visit(request):
    if request.method == "POST":
        patient_id = request.POST.get("patient_id")

        if not patient_id:
            messages.error(request, "No patient selected.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            patient = CustomUser.objects.get(id=patient_id, account_type='patient')
        except CustomUser.DoesNotExist:
            messages.error(request, "Patient not found.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        if not request.user.hospital:
            messages.error(request, "You do not have a hospital assigned to your account.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Create Visit
        visit = Visit.objects.create(
            patient=patient,
            hospital=request.user.hospital,
            stage='billing'
        )

        # Create Bill
        try:
            Bill.objects.create(
                visit=visit,
                patient=patient,
                description="Consultation Fee",
                amount=Decimal("1000.00"),  # Example fee — adjust as needed
                date=timezone.now(),
                status='pending',
            )
            messages.success(request, f"Triage visit and bill created for {patient.patient_name}.")
        except Exception as e:
            messages.error(request, f"Visit created, but failed to create bill: {e}")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    messages.error(request, "Invalid request method.")
    return redirect('patient_list')




def patient_list(request):
   patients = CustomUser.objects.filter(account_type='patient').select_related('hospital')
   return render(request, 'registration/patient_list.html', {'patients': patients})

def registration_dashboard(request):
    return render(request, 'registration/dashboard.html')

def registration(request):

    default_hospital = request.user.hospital

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register_user')

        try:
            user = CustomUser(
                email=email,
                username=username,
                password=make_password(password1),
                account_type='patient',
                hospital=default_hospital,
                patient_name=request.POST.get('patient_name'),
                date_of_birth=request.POST.get('date_of_birth') or None,
                gender=request.POST.get('gender'),
                nationality=request.POST.get('nationality'),
                phone_number=request.POST.get('phone_number'),
                residence=request.POST.get('residence'),
                town=request.POST.get('town'),
                county=request.POST.get('county'),
                country=request.POST.get('country'),
                mother_name=request.POST.get('mother_name'),
                father_name=request.POST.get('father_name'),
                next_of_kin_name=request.POST.get('next_of_kin_name'),
                next_of_kin_residential_address=request.POST.get('next_of_kin_residential_address'),
                next_of_kin_phone_number=request.POST.get('next_of_kin_phone_number'),
                next_of_kin_email=request.POST.get('next_of_kin_email'),
                next_of_kin_relationship=request.POST.get('next_of_kin_relationship')
            )
            user.save()
            messages.success(request, "Patient registered successfully.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Error occurred: {e}")
            return redirect(patient_list)

    return render(request, 'registration/add_patient.html', {'default_hospital': default_hospital})