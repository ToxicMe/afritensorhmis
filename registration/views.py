from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import *
from hospital.models import Hospital
from billing.models import Bill
from django.utils import timezone
from .models import Visit
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from billing.bills_processor import create_bill
from django.utils.timezone import now
from decimal import Decimal, InvalidOperation
from triage.models import *
from doctor.models import *
from pharmacy.models import *
from billing.models import *
from laboratory.models import *
from django.http import JsonResponse
from django.urls import reverse
from billing.utils import create_patient_bill 

def remove_insurance_info(request, insurance_id):
    insurance = get_object_or_404(InsuranceInformation, id=insurance_id)

    if request.method == 'POST':
        insurance.delete()
        messages.success(request, "Insurance information removed successfully.")
        return redirect('view_patient', insurance.user.id)  # Make sure this URL name exists

    messages.error(request, "Invalid request.")
    return redirect('view_patient', insurance.user.id)

# Create your views here.
def visit_detail(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)

    triage = Triage.objects.filter(visit=visit).last()
    doctor_notes = DoctorNote.objects.filter(visit=visit)
    prescription = PrescriptionNote.objects.filter(visit=visit).last()
    sales = Sale.objects.filter(visit=visit)
    bills = Bill.objects.filter(visit=visit)
    lab_results = TestResult.objects.filter(visit=visit)
    providers = InsuranceProvider.objects.all()



    return render(request, 'registration/visit_detail.html', {
        'insurance_providers': providers,
        'visit': visit,
        'triage': triage,
        'doctor_notes': doctor_notes,
        'prescription': prescription,
        'sales': sales,
        'bills': bills,
        'lab_results': lab_results,
    })

def add_insurance_info(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, account_type='patient')
    providers = InsuranceProvider.objects.all()
    errors = {}

    if request.method == 'POST':
        provider_id = request.POST.get('insurance_provider')
        card_number = request.POST.get('card_number')
        scheme_type = request.POST.get('scheme_type')
        principal_name = request.POST.get('principal_name')
        relationship = request.POST.get('relationship_to_principal')
        employer_name = request.POST.get('employer_name', '')
        employer_code = request.POST.get('employer_code', '')
        sha_number = request.POST.get('sha_number', '')
        sha_proof = request.FILES.get('sha_contribution_proof')
        pre_auth_code = request.POST.get('pre_authorization_code', '')
        auth_letter = request.FILES.get('authorization_letter')
        auth_date = request.POST.get('authorization_date')
        approved_amount_raw = request.POST.get('approved_amount')

        # Validate required fields
        if not provider_id:
            errors['insurance_provider'] = "Insurance provider is required."
        if not card_number:
            errors['card_number'] = "Card number is required."
        if not scheme_type:
            errors['scheme_type'] = "Scheme type is required."
        if not principal_name:
            errors['principal_name'] = "Principal member name is required."
        if not relationship:
            errors['relationship_to_principal'] = "Relationship to principal is required."

        # Optional: Validate approved amount is a number
        approved_amount = None
        if approved_amount_raw:
            try:
                approved_amount = Decimal(approved_amount_raw)
            except InvalidOperation:
                errors['approved_amount'] = "Approved amount must be a valid number."

        if not errors:
            # Save the record
            InsuranceInformation.objects.create(
                user=patient,
                insurance_provider_id=provider_id,
                card_number=card_number,
                scheme_type=scheme_type,
                principal_name=principal_name,
                relationship_to_principal=relationship,
                employer_name=employer_name,
                employer_code=employer_code,
                sha_number=sha_number,
                sha_contribution_proof=sha_proof,
                pre_authorization_code=pre_auth_code,
                authorization_letter=auth_letter,
                authorization_date=auth_date if auth_date else None,
                approved_amount=approved_amount,
            )

            messages.success(request, "Insurance information saved successfully.")
            return redirect('view_patient', patient_id=patient.id)
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, 'registration/add_insurance_info.html', {
        'patient': patient,
        'providers': providers,
        'errors': errors,
        'input': request.POST,
    })



def view_patient(request, patient_id):
    providers = InsuranceProvider.objects.filter(is_active=True)
    patient = get_object_or_404(CustomUser, id=patient_id, account_type='patient')
    visits = Visit.objects.filter(patient=patient).order_by('-date_time')
    insurance = InsuranceInformation.objects.filter(user=patient)


    context = {
        'insurance_providers': providers,
        'patient': patient,
        'visits': visits,
        'insurance': insurance,
    }
    return render(request, 'registration/view_patient.html', context)


def view_patient_visits(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id)
    visits = Visit.objects.filter(patient=patient).order_by('-date_time')
    return render(request, 'registration/patient_visits.html', {'patient': patient, 'visits': visits})




def create_visit(request):
    if request.method != "POST":
        return JsonResponse({'error': "Invalid request method."}, status=405)

    patient_id = request.POST.get("patient_id")
    visit_type = request.POST.get("type")
    discounted = request.POST.get("discounted") == "on"
    discount_reason = request.POST.get("discount_reason", "").strip()
    custom_amount_input = request.POST.get("custom_amount", "").strip()

    if not patient_id:
        return JsonResponse({'error': "No patient selected."}, status=400)

    patient = get_object_or_404(CustomUser, id=patient_id, account_type='patient')

    if not request.user.hospital:
        return JsonResponse({'error': "You do not have a hospital assigned to your account."}, status=403)

    # ✅ Check for existing active visit
    ongoing_visit = Visit.objects.filter(
        patient=patient,
        hospital=request.user.hospital
    ).exclude(stage='discharged').first()

    if ongoing_visit:
        return JsonResponse({
            'warning': f"{patient.patient_name} already has an active visit.",
            'redirect_url': reverse('view_patient', args=[patient.id])
        }, status=200)

    # ✅ Determine initial stage
    stage_map = {
        'outpatient': 'billing',
        'outpatient_consultation': 'consultation',
        'inpatient': 'inpatient',
        'minor_surgery': 'minor_surgery',
    }
    initial_stage = stage_map.get(visit_type, 'billing')

    # ✅ Create Visit
    visit = Visit.objects.create(
        patient=patient,
        hospital=request.user.hospital,
        type=visit_type,
        stage=initial_stage
    )

    # ✅ Conditionally create bill
    if visit_type not in ['outpatient_consultation', 'minor_surgery', 'inpatient']:
        try:
            amount = Decimal("1000.00")
            if custom_amount_input:
                try:
                    amount = Decimal(custom_amount_input)
                except InvalidOperation:
                    return JsonResponse({'error': "Invalid custom amount."}, status=400)

            bill, error = create_patient_bill(
                visit=visit,
                patient=patient,
                description="Consultation Fee",
                amount=amount,
                discounted=discounted,
                custom_amount=custom_amount_input if custom_amount_input else None,
                discount_reason=discount_reason
            )

            if bill:
                return JsonResponse({
                    'success': f"{visit.get_type_display()} visit and bill created successfully."
                })
            else:
                return JsonResponse({
                    'error': f"Visit created, but failed to create bill: {error}"
                }, status=500)

        except Exception as e:
            return JsonResponse({
                'error': f"Visit created, but failed to create bill: {str(e)}"
            }, status=500)

    # ✅ If no billing required
    return JsonResponse({
        'success': f"{visit.get_type_display()} visit created successfully."
    })




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
        id_number = request.POST.get('id_number')  # <- add this

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('registration')

        if id_number:
            if CustomUser.objects.filter(id_number=id_number).exists():
                messages.error(request, "A patient with this ID number already exists.")
                return redirect('registration')

        try:
            user = CustomUser(
                email=email,
                username=username,
                password=make_password(password1),
                id_number=id_number,  # <- include in model
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
            return redirect('patient_list')

        except Exception as e:
            messages.error(request, f"Error occurred: {e}")
            return redirect('registration')

    return render(request, 'registration/add_patient.html', {'default_hospital': default_hospital})
