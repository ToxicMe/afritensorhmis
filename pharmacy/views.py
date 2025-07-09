from django.shortcuts import render, get_object_or_404, redirect
from registration.models import Visit
from doctor.models import PrescriptionNote  
from django.contrib import messages
from django.db import IntegrityError
from django.utils.timezone import now
from .models import *
from accounts.models import CustomUser
from django.db import transaction
from decimal import Decimal






# Create your views here.
def pharmacy(request):
    return render(request, 'pharmacy/dashboard.html')


def view_prescription_note(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)
    prescription = PrescriptionNote.objects.filter(visit=visit).last()
    products = Product.objects.filter(
        consignment__pharmacy__hospital_name=visit.hospital,
        quantity__gt=0
    )

    return render(request, 'pharmacy/view_prescription_note.html', {
        'visit': visit,
        'prescription': prescription,
        'products': products
    })

def pharmacy_visits_list(request):
    user = request.user

    if not user.hospital:
        return render(request, 'pharmacy/pharmacy_visits_list.html', {
            'visits': [],
            'error': 'No hospital associated with your account.'
        })

    visits = Visit.objects.filter(
        stage='pharmacy',
        hospital=user.hospital
    ).order_by('-updated_on')  # latest first

    return render(request, 'pharmacy/pharmacy_visits_list.html', {
        'visits': visits
    })



########################## SALES FUNCTIONS ##########################

def add_product(request):
    consignments = Consignment.objects.all()
  

    if request.method == 'POST':
        name = request.POST.get('name')
        consignment_id = request.POST.get('consignment')
        acquiring_price = request.POST.get('acquiring_price')
        selling_price = request.POST.get('selling_price')
        quantity = request.POST.get('quantity')
        expiry_date = request.POST.get('expiry_date')
        description = request.POST.get('description')
    
        # Validate required fields
        if not all([name, consignment_id, acquiring_price, selling_price, quantity, expiry_date]):
            messages.error(request, "All fields except description are required.")
            return render(request, 'pharmacy/add_product.html', {'consignments': consignments})

        try:
            consignment = Consignment.objects.get(id=consignment_id)

            product = Product(
                name=name,
                consignment=consignment,
                acquiring_price=acquiring_price,
                selling_price=selling_price,
                quantity=quantity,
                expiry_date=expiry_date,
                description=description,
                done_by=request.user,
                created_at=timezone.now()
            )

            product.save()
            messages.success(request, "Product added successfully.")
            return redirect(pharmacy)  # Adjust as needed

        except Consignment.DoesNotExist:
            messages.error(request, "Invalid consignment selected.")
        except IntegrityError:
            messages.error(request, "A product with this name or SKU already exists.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

    return render(request, 'pharmacy/add_product.html', {'consignments': consignments})




@transaction.atomic
def add_sale_from_prescription(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)
    patient = visit.patient
    user = request.user

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 0))

        product = get_object_or_404(Product, id=product_id)

        if quantity <= 0:
            messages.error(request, "Quantity must be a positive number.")
            return redirect('view_prescription_note', tracking_code=tracking_code)

        if product.quantity < quantity:
            messages.error(request, "Not enough stock available for this product.")
            return redirect('view_prescription_note', tracking_code=tracking_code)

        # Get or create a Sale
        sale, created = Sale.objects.get_or_create(
            patient=patient,
            visit=visit,
            defaults={
                'amount': 0,
                'payment_method': 'cash',
                'status': 'pending',
                'done_by': user
            }
        )

        # Create SaleItem
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            price=product.selling_price
        )

        # Deduct stock
        product.quantity -= quantity
        product.save()

        # Update sale total
        sale.amount += Decimal(product.selling_price) * quantity
        sale.save()

        messages.success(request, "Product added to sale.")
        return redirect('view_prescription_note', tracking_code=tracking_code)

    messages.error(request, "Invalid request.")
    return redirect('view_prescription_note', tracking_code=tracking_code)
