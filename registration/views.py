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
from django.db.models import Count
import json
from datetime import timedelta
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear



from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Visit
import json

from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json

def main_dashboard(request):
    period = request.GET.get('period', 'day')  # day, week, month, year
    today = timezone.now()

    if period == 'day':
        start_date = today - timedelta(days=6)
        visits = Visit.objects.filter(date_time__date__gte=start_date)
        data = visits.extra({'day': "date(date_time)"}).values('day').annotate(count=Count('id')).order_by('day')
        labels = [str(v['day']) for v in data]  # remove strftime
        counts = [v['count'] for v in data]

    elif period == 'week':
        start_date = today - timedelta(weeks=6)
        visits = Visit.objects.filter(date_time__date__gte=start_date)
        data = visits.extra({'week': "strftime('%%Y-%%W', date_time)"}).values('week').annotate(count=Count('id')).order_by('week')
        labels = [v['week'] for v in data]
        counts = [v['count'] for v in data]

    elif period == 'month':
        start_date = today - timedelta(days=180)
        visits = Visit.objects.filter(date_time__date__gte=start_date)
        data = visits.extra({'month': "strftime('%%Y-%%m', date_time)"}).values('month').annotate(count=Count('id')).order_by('month')
        labels = [v['month'] for v in data]
        counts = [v['count'] for v in data]

    elif period == 'year':
        start_year = today.year - 5
        visits = Visit.objects.filter(date_time__year__gte=start_year)
        data = visits.extra({'year': "strftime('%%Y', date_time)"}).values('year').annotate(count=Count('id')).order_by('year')
        labels = [v['year'] for v in data]
        counts = [v['count'] for v in data]

    # Gender data
    gender_data = visits.values('patient__gender').annotate(count=Count('id'))
    gender_labels = [g['patient__gender'].capitalize() for g in gender_data]
    gender_counts = [g['count'] for g in gender_data]

    context = {
        'labels': json.dumps(labels),
        'counts': json.dumps(counts),
        'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        'selected_period': period
    }

    return render(request, 'index.html', context)





def remove_insurance_info(request, insurance_id):
    insurance = get_object_or_404(InsuranceInformation, id=insurance_id)

    if request.method == 'POST':
        insurance.delete()
        messages.success(request, "Insurance information removed successfully.")
        return redirect('view_patient', insurance.user.id)  # Make sure this URL name exists

    messages.error(request, "Invalid request.")
    return redirect('view_patient', insurance.user.id)

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
    if request.method == "GET":
        patient_id = request.GET.get("patient_id")
        if not patient_id:
            return redirect("patient_list")

        patient = get_object_or_404(CustomUser, id=patient_id, account_type='patient')

        return render(request, "registration/create_visit.html", {
            "patient": patient,
        })

    elif request.method == "POST":
        # Extract POST data
        patient_id = request.POST.get("patient_id")
        visit_type = request.POST.get("type")
        discounted = request.POST.get("discounted") == "on"
        discount_reason = request.POST.get("discount_reason", "").strip()
        custom_amount_input = request.POST.get("custom_amount", "").strip()

        # Validate patient selection
        if not patient_id:
            return JsonResponse({'error': "No patient selected."}, status=400)

        # Fetch patient
        patient = get_object_or_404(CustomUser, id=patient_id, account_type='patient')

        # Validate hospital
        if not request.user.hospital:
            return JsonResponse({'error': "You do not have a hospital assigned to your account."}, status=403)

        # Prevent duplicate active visit
        ongoing_visit = Visit.objects.filter(
            patient=patient,
            hospital=request.user.hospital
        ).exclude(stage='discharged').first()

        if ongoing_visit:
            return JsonResponse({
                'warning': f"{patient.get_full_name()} already has an active visit.",
                'redirect_url': reverse('view_patient', args=[patient.id])
            })

        # Determine initial stage based on visit type
        stage_map = {
            'outpatient': 'billing',
            'outpatient_consultation': 'consultation',
            'inpatient': 'inpatient',
            'minor_surgery': 'minor_surgery',
        }
        initial_stage = stage_map.get(visit_type, 'billing')

        # Create the visit
        visit = Visit.objects.create(
            patient=patient,
            hospital=request.user.hospital,
            type=visit_type,
            stage=initial_stage
        )

        # Auto-create bill if billing is required
        if visit_type not in ['outpatient_consultation', 'minor_surgery', 'inpatient']:
            try:
                # Parse or override amount
                amount = Decimal("1000.00")
                if custom_amount_input:
                    try:
                        amount = Decimal(custom_amount_input)
                    except InvalidOperation:
                        return JsonResponse({'error': "Invalid custom amount."}, status=400)

                # Create bill
                bill, error = create_patient_bill(
                    visit=visit,
                    patient=patient,
                    description="Consultation Fee",
                    amount=amount,
                    discounted=discounted,
                    custom_amount=custom_amount_input or None,
                    discount_reason=discount_reason,
                    created_by=request.user,
                )

                if bill:
                    return JsonResponse({
                        'success': f"{visit.get_type_display()} visit created successfully.",
                        'bill_created': True,
                        'bill_id': bill.id,
                        'bill_amount': str(bill.amount),
                        'bill_description': bill.description,
                        'patient_name': patient.get_full_name(),
                    })

                else:
                    return JsonResponse({
                        'error': f"Visit created, but failed to create bill: {error}"
                    }, status=500)

            except Exception as e:
                return JsonResponse({
                    'error': f"Visit created, but failed to create bill: {str(e)}"
                }, status=500)

        # If no billing required
        return JsonResponse({
            'success': f"{visit.get_type_display()} visit created successfully.",
            'bill_created': False,
        })

    return JsonResponse({'error': "Invalid request method."}, status=405)


def patient_list(request):
    # Order patients by most recent first
    patients = (
        CustomUser.objects
        .filter(account_type='patient')
        .select_related('hospital')
        .order_by('-id')  # or use '-created_at' if you have that field
    )

    # Check if we need to show the modal
    new_patient_id = request.GET.get('new_patient_id')
    show_modal = False
    modal_message = None
    patient_id = None

    if new_patient_id:
        show_modal = True
        modal_message = "Patient registered successfully."
        patient_id = new_patient_id

    return render(
        request,
        'registration/patient_list.html',
        {
            'patients': patients,
            'show_modal': show_modal,
            'modal_message': modal_message,
            'new_patient_id': patient_id,
        }
    )




def registration_dashboard(request):
    return render(request, 'registration/dashboard.html')



def registration(request):
    default_hospital = request.user.hospital

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        id_number = request.POST.get('id_number')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register_patient')

        if id_number and CustomUser.objects.filter(id_number=id_number).exists():
            messages.error(request, "A patient with this ID number already exists.")
            return redirect('register_patient')

        try:
            user = CustomUser(
                password=make_password(password1),
                id_number=id_number,
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

            # Redirect with patient_id in querystring
            return redirect(f"{reverse('patient_list')}?new_patient_id={user.id}")

        except Exception as e:
            messages.error(request, f"Error occurred: {e}")
            return redirect('register_patient')

    return render(request, 'registration/add_patient.html', {'default_hospital': default_hospital})
