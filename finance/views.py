from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
User = get_user_model()
from django.utils.timezone import now
from .models import *
from django.core.paginator import Paginator

def add_fixed_asset(request):
    hospitals = Hospital.objects.all()
    if request.method == 'POST':
        try:
            asset = FixedAsset.objects.create(
                asset=request.POST.get('asset'),
                asset_class=request.POST.get('asset_class'),
                purchase_date=request.POST.get('purchase_date'),
                disposal_date=request.POST.get('disposal_date') or None,
                description=request.POST.get('description'),
                cost=request.POST.get('cost') or 0,
                additions=request.POST.get('additions') or 0,
                disposal=request.POST.get('disposal') or 0,
                total_asset=request.POST.get('total_asset') or 0,
                opening_depreciation=request.POST.get('opening_depreciation') or 0,
                depreciation_year=request.POST.get('depreciation_year') or 0,
                depreciation_deletion=request.POST.get('depreciation_deletion') or 0,
                total_depreciation=request.POST.get('total_depreciation') or 0,
                net_book_value=request.POST.get('net_book_value') or 0,
                currency=request.POST.get('currency'),
                done_by=request.user,
                hospital=request.user.hospital  # Assuming this relation exists
            )
            messages.success(request, f"Asset {asset.asset} added successfully.")
        except Exception as e:
            messages.error(request, f"Error saving asset: {str(e)}")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('finance/financial_management/fixed_assets.html', {'hospitals': hospitals})

def purchase_order_create(request):
    if request.method == 'POST':
        po = PurchaseOrder.objects.create(
            supplier_id=request.POST.get('supplier'),
            requisition_id=request.POST.get('requisition') or None,
            expected_delivery_date=request.POST.get('expected_delivery_date'),
            total_amount=request.POST.get('total_amount') or 0,
            payment_terms=request.POST.get('payment_terms'),
            delivery_location=request.POST.get('delivery_location'),
            notes=request.POST.get('notes'),
            created_by=request.user,
        )
        messages.success(request, "Purchase Order created successfully.")
    return redirect('purchase_order_list')


def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            po.status = "approved"
            po.save()
            messages.success(request, "Purchase Order approved.")
        elif action == "reject":
            reason = request.POST.get("rejection_reason")
            po.status = "cancelled"
            po.rejection_reason = reason
            po.save()
            messages.error(request, f"Purchase Order rejected: {reason}")
        return redirect("purchase_order_list")

    return render(request, "finance/purchasing/purchase_order_detail.html", {"purchase_order": po})


def purchase_order_list(request):
    supplier_id = request.GET.get('supplier')
    status = request.GET.get('status')

    purchase_orders = PurchaseOrder.objects.all()

    if supplier_id:
        purchase_orders = purchase_orders.filter(supplier_id=supplier_id)
    if status:
        purchase_orders = purchase_orders.filter(status=status)

    purchase_orders = purchase_orders.order_by('-order_date')

    paginator = Paginator(purchase_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    suppliers = Supplier.objects.all()

    return render(request, 'finance/purchasing/purchase_order_list.html', {
        'page_obj': page_obj,
        'suppliers': suppliers,
        'requisitions': Requisition.objects.all(), 
        'filter_supplier': supplier_id,
        'filter_status': status
    })


def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    return render(request, 'finance/adminstration/supplier_detail.html', {'supplier': supplier}) 



def requisition_create(request):
    if request.method == 'POST':
        try:
            print("Request POST:", request.POST)

            user_id = request.POST.get('user')
            if not user_id:
                raise ValueError("User ID missing")

            user = User.objects.get(id=user_id)
            print("User resolved:", user)

            requisition = Requisition.objects.create(
                user=user,
                job_title=request.POST.get('job_title'),
                department=request.POST.get('department'),
                email=request.POST.get('email'),
                date_of_request=request.POST.get('date_of_request'),
                is_urgent=request.POST.get('is_urgent') == 'True',
                notes=request.POST.get('notes', ''),
                done_by=request.user,
            )
            print("Requisition created:", requisition)

            # Item lists
            descriptions = request.POST.getlist('item_description[]')
            units = request.POST.getlist('unit[]')
            quantities = request.POST.getlist('quantity[]')

            for desc, unit, qty in zip(descriptions, units, quantities):
                if desc.strip() and unit.strip() and qty:
                    RequisitionItem.objects.create(
                        requisition=requisition,
                        item_description=desc,
                        unit=unit,
                        quantity=int(qty)
                    )
            print("Items created.")

            messages.success(request, "Requisition created successfully.")
            return redirect('requisition_list')

        except Exception as e:
            import traceback
            traceback.print_exc()  # 🔥 Show full traceback
            messages.error(request, "There was an error processing the requisition.")
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
    hospitals = Hospital.objects.all()
    return render(request, 'finance/financial_management/fixed_assets.html',  {'hospitals': hospitals})



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