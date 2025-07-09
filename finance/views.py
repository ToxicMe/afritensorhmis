from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.
def requisition_create(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('name')  # 'name' is now user ID from dropdown
            user_instance = User.objects.get(id=user_id)

            requisition = Requisition.objects.create(
                name=user_instance,
                job_title=request.POST.get('job_title'),
                department=request.POST.get('department'),
                email=request.POST.get('email'),
                date_of_request=request.POST.get('date_of_request'),
                is_urgent=request.POST.get('is_urgent') == 'True',
                notes=request.POST.get('notes'),
                done_by=request.user  # current logged-in user
            )

            # Handle items if you added them in the form (optional)
            # Example: loop over POST data to create RequisitionItem

            messages.success(request, "Requisition created successfully.")
        except User.DoesNotExist:
            messages.error(request, "Selected user does not exist.")
        return redirect('requisition_list')
    
    return redirect('requisition_list')


def requisition_list(request):
    requisitions = Requisition.objects.all()
    users = User.objects.all()
    return render(request, 'finance/requisition_management/requisition_list.html', {
        'requisitions': requisitions,
        'users': users
    })

def requisition_detail(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    return render(request, 'finance/requisition_management/requisition_detail.html', {'requisition': requisition})


def approve_requisition(request, pk):
    # Add approval logic if needed (e.g. updating a status field)
    return redirect('requisition_detail', pk=pk)

def add_supplier(request):
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST['name'],
            contact_person=request.POST.get('contact_person'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            tax_id=request.POST.get('tax_id'),
            bank_name=request.POST.get('bank_name'),
            payment_terms=request.POST.get('payment_terms'),
            done_by=request.user,
        )
    return redirect('supplier_list')

def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('-created_at')
    return render(request, 'finance/adminstration/suppliers_list.html', {'suppliers': suppliers})

def accounting(request):
    return render(request, 'finance/dashboard.html')

def cash_flow(request):
    return render(request, 'finance/financial_management/cash_flow.html')

def general_ledger(request):
    return render(request, 'finance/financial_management/general_ledger.html')

def balance_sheet(request):
    return render(request, 'finance/financial_management/balance_sheet.html')

def trial_balance(request):
    return render(request, 'finance/financial_management/trial_balance.html')


def receivables(request):
    return render(request, 'finance/financial_management/receivables.html')

def receivables_details(request):
    return render(request, 'finance/financial_management/receivables_details.html')



def payables(request):
    return render(request, 'finance/financial_management/payables.html')

def fixed_assets(request):
    return render(request, 'finance/financial_management/fixed_assets.html')



def payables_details(request):
    return render(request, 'finance/financial_management/payables_details.html')

def cash_management(request):
    return render(request, 'finance/financial_management/cash_management.html')

def moh_dashboard(request):
    return render(request, 'moh_reports/dashboard.html')


def outpatient_register(request):
    return render(request, 'moh_reports/outpatient_register.html')

def xray_register(request):
    return render(request, 'moh_reports/xray_register.html')

def laboratory_register(request):
    return render(request, 'moh_reports/laboratory_register.html')

def inpatient_register(request):
    return render(request, 'moh_reports/inpatient_register.html')

def preart_register(request):
    return render(request, 'moh_reports/preart_register.html')

def preart_care_register(request):
    return render(request, 'moh_reports/preart_care_register.html')

def art_register(request):
    return render(request, 'moh_reports/art_register.html')

def htc_lab_register(request):
    return render(request, 'moh_reports/htc_lab_register.html')

def maternity_register(request):
    return render(request, 'moh_reports/maternity_register.html')

def sgbv_register(request):
    return render(request, 'moh_reports/sgbv_register.html')

def daily_activity_register(request):
    return render(request, 'moh_reports/daily_activity_register.html')