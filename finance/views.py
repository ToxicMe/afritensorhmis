from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count, Case, When, F, DecimalField, ExpressionWrapper
from decimal import Decimal
from django.utils import timezone
from django.utils.timezone import now
from .models import *
from django.core.paginator import Paginator
from billing.models import Bill, PaymentReceipt
from .utils import *

User = get_user_model()



def accounts_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        hospital_id = request.POST.get('hospital')
        account_number = request.POST.get('account_number')
        account_type = request.POST.get('account_type')
        currency = request.POST.get('currency')
        balance = request.POST.get('balance', 0.00)
        is_active = request.POST.get('is_active') == 'on'

        try:
            hospital = Hospital.objects.get(id=hospital_id)
            CashAccount.objects.create(
                name=name,
                hospital=hospital,
                account_number=account_number,
                account_type=account_type,
                currency=currency,
                balance=balance,
                is_active=is_active,
                done_by=request.user
            )
            messages.success(request, "Account added successfully!")
        except Hospital.DoesNotExist:
            messages.error(request, "Invalid hospital selected.")

        return redirect('cash_accounts_list')

    accounts = CashAccount.objects.all().order_by('-created_at')
    hospitals = Hospital.objects.all()
    return render(request, 'finance/cash_office/accounts/accounts_list.html', {
        'accounts': accounts,
        'hospitals': hospitals
    })


def accounts_detail(request, pk):
    account = get_object_or_404(CashAccount, pk=pk)
    return render(request, 'finance/cash_office/accounts/accounts_detail.html', {'account': account})

def bank_accounts(request):
   
    return render(request, 'finance/cash_office/accounts/dashboard.html')

def income_statement(request):
   

    return render(request, 'finance/financial_management/income_statement.html')

def pending_insurance_receipts(request):
    insurance_receipts = PaymentReceipt.objects.filter(
        payment_method='insurance',
        status='pending'
    ).order_by('-date_created')


    return render(request, 'finance/insurance/insurance_receipts.html', {
        'insurance_receipts': insurance_receipts,
    })

def insurance_payment_receipts(request):
    insurance_receipts = PaymentReceipt.objects.filter(payment_method='insurance').order_by('-date_created')

    total_insurance_amount = insurance_receipts.count()  # or compute custom totals based on bills if needed

    return render(request, 'finance/insurance/insurance_receipts.html', {
        'insurance_receipts': insurance_receipts,
        'total_insurance_amount': total_insurance_amount,
    })

def view_petty_cash_entry(request, entry_id):
    entry = get_object_or_404(PettyCashEntry, id=entry_id)
    return render(request, 'finance/cash_office/petty_cash_entry_detail.html', {'entry': entry})

def add_petty_cash_entry(request):
    if request.method == "POST":
        entry = PettyCashEntry(
            date=request.POST.get("date"),
            description=request.POST.get("description"),
            amount=request.POST.get("amount"),
            paid_to=request.POST.get("paid_to"),
            approved_by=request.POST.get("approved_by"),
            received_by=request.POST.get("received_by"),
            reference=request.POST.get("reference"),
            entry_type=request.POST.get("entry_type"),
            done_by=request.user
        )
        entry.save()
        return redirect('petty_cash') 

def petty_cash(request):
    users = User.objects.exclude(account_type='Patient')  

    entries = PettyCashEntry.objects.all().order_by('-date')

    return render(request, 'finance/cash_office/petty_cash_journal.html',{'entries': entries,  'users': users})

def add_fixed_asset(request):
    hospitals = Hospital.objects.all()

    if request.method == 'POST':
        try:
            hospital_id = request.POST.get('hospital')
            hospital = Hospital.objects.get(id=hospital_id)

            asset = FixedAsset.objects.create(
                asset_id=request.POST.get('asset_id'),
                asset_class=request.POST.get('asset_class'),
                purchase_date=request.POST.get('purchase_date'),
                disposal_date=request.POST.get('disposal_date') or None,
                hospital=hospital,
                description=request.POST.get('description') or '',
                cost=Decimal(request.POST.get('cost') or 0),
                additions=Decimal(request.POST.get('additions') or 0),
                disposal_value=Decimal(request.POST.get('disposal_value') or 0),
                opening_depreciation=Decimal(request.POST.get('opening_depreciation') or 0),
                depreciation_for_year=Decimal(request.POST.get('depreciation_for_year') or 0),
                depreciation_on_disposal=Decimal(request.POST.get('depreciation_on_disposal') or 0),
                done_by=request.user,
            )
            # total_asset and net_book_value will auto-calculate in save()
            messages.success(request, f"Asset {asset.asset_id} added successfully.")
        except Hospital.DoesNotExist:
            messages.error(request, "Selected hospital not found.")
        except Exception as e:
            messages.error(request, f"Error saving asset: {str(e)}")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, 'finance/financial_management/fixed_assets.html', {'hospitals': hospitals})

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
    User = get_user_model()
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




def payments(request):
    bills = Bill.objects.all()

    # --- Filters ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status', 'paid')  # default to 'paid'
    query = request.GET.get('q')

    if start_date:
        bills = bills.filter(date__gte=start_date)
    if end_date:
        bills = bills.filter(date__lte=end_date)

    if status:
        bills = bills.filter(status=status)

    if query:
        bills = bills.filter(
            Q(transaction_id__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )

    # --- Aggregation ---
    total_paid_amount = bills.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # --- Pagination ---
    paginator = Paginator(bills, 20)  # 20 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/cash_office/payments.html', {
        'page_obj': page_obj,
        'total_paid_amount': total_paid_amount,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'query': query,
    })

def cash_flow(request):
    return render(request, 'finance/financial_management/cash_flow.html')

def general_ledger(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        account_number = request.POST.get('account_number')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        entry_type = request.POST.get('entry_type')
        text = request.POST.get('text')
        reference = request.POST.get('reference')

    try:
        entry = LedgerEntry.objects.create(
                date=date,
                account_number=account_number,
                description=description,
                amount=amount,
                entry_type=entry_type,
                text=text,
                reference=reference,
                entry_by=request.user
            )
        entry.save()
        messages.success(request, "Ledger entry saved successfully.")
        return redirect('general_ledger')  # Adjust to match your URL name
    except Exception as e:
        messages.error(request, f"Error saving entry: {str(e)}")

    # For GET request, fetch existing entries
    entries = LedgerEntry.objects.all()
    return render(request, 'finance/financial_management/general_ledger.html',{'entries':entries})

def balance_sheet(request):
    return render(request, 'finance/financial_management/balance_sheet.html')

def trial_balance(request):
    petty_cash_total_debit = get_total_petty_cash_debit()
    total_pharmacy_bills = get_total_pharmacy_bills()
    total_leasehold_value = get_total_leasehold_value()
    total_computers_value = get_total_computers_value()
    total_net_book_value = get_total_net_book_value()
    total_insurance_bills = get_total_insurance_bills()
    total_consultation_bills = get_total_consultation_bills()
    total_test_bills = get_total_test_bills()

    return render(request, 'finance/financial_management/trial_balance.html', {'total_computers_value': total_computers_value, 
                                                                               'total_net_book_value': total_net_book_value, 
                                                                               'total_leasehold_value': total_leasehold_value, 
                                                                               'total_insurance_bills':total_insurance_bills,
                                                                               'petty_cash_total_debit':petty_cash_total_debit,
                                                                               'total_pharmacy_bills': total_pharmacy_bills,
                                                                               'total_consultation_bills': total_consultation_bills,
                                                                               'total_test_bills': total_test_bills,
                                                                               
                                                                               })


def receivables(request):
    # Start with all insurance bills
    insurance_bills = Bill.objects.filter(payment_method='insurance')

    # Get filter values
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    query = request.GET.get('q')

    # Apply filters
    if start_date:
        insurance_bills = insurance_bills.filter(date__date__gte=start_date)
    if end_date:
        insurance_bills = insurance_bills.filter(date__date__lte=end_date)
    if status:
        insurance_bills = insurance_bills.filter(status=status)
    if query:
        insurance_bills = insurance_bills.filter(
            Q(transaction_id__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(patient__username__icontains=query)
        )

    # Calculate total insurance amount
    total_insurance_amount = insurance_bills.aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'finance/financial_management/receivables.html', {
        'insurance_bills': insurance_bills,
        'total_insurance_amount': total_insurance_amount,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'query': query
    })

def receivables_details(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    return render(request, 'finance/financial_management/receivables_details.html', {
        'bill': bill,
        'customer': bill.patient,
    })

def profitandloss(request):
    total_insurance_bills = get_total_insurance_bills()
    total_all_bills = get_total_all_bills()
    total_pharmacy_bills = get_total_pharmacy_bills()
    total_consultation_bills = get_total_consultation_bills()
    total_test_bills = get_total_test_bills()



    return render(request, 'finance/financial_management/profitandloss.html', {
        'total_insurance_bills': total_insurance_bills,
        'total_all_bills': total_all_bills,
        'total_pharmacy_bills': total_pharmacy_bills,
        'total_consultation_bills': total_consultation_bills,
        'total_test_bills': total_test_bills,
    })


def payables(request):
    return render(request, 'finance/financial_management/payables.html')

def fixed_assets(request):
    hospitals = Hospital.objects.all()
    assets = FixedAsset.objects.all().order_by('-created_at')  # Latest first
    return render(request, 'finance/financial_management/fixed_assets.html', {
        'hospitals': hospitals,
        'assets': assets
    })



def insurance(request):
    return render(request, 'finance/insurance/dashboard.html')

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