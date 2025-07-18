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
from billing.models import Bill
from django.db.models import Q, Sum, Max
from django.views.decorators.http import require_POST






# Create your views here.
def pharmacy(request):
    return render(request, 'pharmacy/dashboard.html')



def view_walkin_bill(request, transaction_id):
    bill = get_object_or_404(Bill, transaction_id=transaction_id)

    # Get all bills that share the same visit or are walk-in (same patient + same transaction)
    if bill.visit:
        bills = Bill.objects.filter(visit=bill.visit)
        visit = bill.visit
    else:
        bills = Bill.objects.filter(patient=bill.patient, transaction_id=transaction_id)
        visit = None

    total_amount = sum(b.amount for b in bills)

    return render(request, 'pharmacy/pharmacy_bill_receipt.html', {
        'bills': bills,
        'patient': bill.patient,
        'visit': visit,
        'total_amount': total_amount,
        'transaction_id': transaction_id,
    })



def pharmacy_unpaid_bills(request):
    # Filter for unpaid bills either from walk-ins (no visit) or with visit at 'billing_pharmacy'
    bills = (
        Bill.objects
        .filter(
            status='pending'
        )
        .filter(
            Q(visit__stage='billing_pharmacy') | Q(visit__isnull=True)
        )
        .values('visit', 'patient__id')
        .annotate(
            total_amount=Sum('amount'),
            latest_date=Max('date'),
            tracking_code=Max('visit__tracking_code'),
            patient_name=Max('patient__first_name'),
            patient_username=Max('patient__username'),
            transaction_id=Max('transaction_id'),
            status=Max('status'),
            description=Max('description'),
        )
        .order_by('-latest_date')
    )

    return render(request, 'pharmacy/pharmacy_unpaid_bills.html', {
        'grouped_bills': bills
    })


@require_POST
def mark_bills_paid_walkin(request, transaction_id):
    payment_method = request.POST.get("payment_method", "cash")
    bills = Bill.objects.filter(transaction_id=transaction_id, visit__isnull=True, status='pending')

    if not bills.exists():
        messages.error(request, "No matching walk-in bills.")
        return redirect("pharmacy_unpaid_bills")

    bills.update(status="paid", payment_method=payment_method)
    messages.success(request, "Walk-in bill marked as paid.")
    return redirect("pharmacy_unpaid_bills")


@transaction.atomic
def walkin_sale_view(request):
    products = Product.objects.filter(quantity__gt=0, consignment__pharmacy__hospital_name=request.user.hospital).distinct()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_item":
            # Store temporary data in session
            item = {
                "product_id": int(request.POST.get("product_id")),
                "quantity": int(request.POST.get("quantity")),
                "description": request.POST.get("description", "")
            }
            cart = request.session.get("walkin_cart", [])
            cart.append(item)
            request.session["walkin_cart"] = cart
            messages.success(request, "Item added to cart.")
            return redirect("walkin_sale")

        elif action == "finalize":
            full_name = request.POST.get("full_name")
            phone = request.POST.get("phone")
            prescription = request.POST.get("prescription")

            if not full_name or not phone or not prescription:
                messages.error(request, "All buyer information is required.")
                return redirect("walkin_sale")

            # Create dummy patient (optional: reuse or check by phone)
            patient, created = CustomUser.objects.get_or_create(
                email=f"{phone}@walkin.local",
                defaults={
                    "username": f"user_{phone}",
                    "patient_name": full_name,
                    "phone_number": phone,
                    "account_type": "patient",
                    "hospital": request.user.hospital,
                }
            )

            cart = request.session.get("walkin_cart", [])
            if not cart:
                messages.error(request, "Cart is empty.")
                return redirect("walkin_sale")

            # Create Sale
            sale = Sale.objects.create(
                patient=patient,
                visit=None,
                done_by=request.user,
                payment_method="cash",  # or let user pick
            )

            total = 0
            for item in cart:
                product = get_object_or_404(Product, id=item["product_id"])
                quantity = item["quantity"]

                if product.quantity < quantity:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    sale.delete()
                    return redirect("walkin_sale")

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=product.selling_price
                )

                product.quantity -= quantity
                product.save()

                total += product.selling_price * quantity

            sale.amount = total
            sale.save()

            # Create Bill for this sale
            Bill.objects.create(
                visit=None,
                patient=patient,
                description=f"Pharmacy walk-in purchase",
                amount=total,
                status="pending"
            )

            # Clear cart
            request.session["walkin_cart"] = []

            messages.success(request, "Walk-in sale completed.")
            return redirect("walkin_sale")

    cart_items = []
    cart = request.session.get("walkin_cart", [])
    for item in cart:
        product = Product.objects.filter(id=item["product_id"]).first()
        if product:
            cart_items.append({
                "product": product,
                "quantity": item["quantity"],
                "description": item.get("description", ""),
                "subtotal": product.selling_price * item["quantity"]
            })

    return render(request, "pharmacy/walkin_sale.html", {
        "products": products,
        "cart_items": cart_items
    })

@transaction.atomic
def view_prescription_note(request, tracking_code):
    visit = get_object_or_404(Visit, tracking_code=tracking_code)
    patient = visit.patient
    prescription = PrescriptionNote.objects.filter(visit=visit).last()

    # Show only products in stock at the current hospital
    products = Product.objects.filter(
        consignment__pharmacy__hospital_name=visit.hospital,
        quantity__gt=0
    ).distinct()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_item":
            product_id = request.POST.get("product_id")
            quantity = int(request.POST.get("quantity"))
            description = request.POST.get("description")

            sale, created = Sale.objects.get_or_create(
                visit=visit,
                patient=patient,
                status='pending',
                defaults={"done_by": request.user}
            )

            product = get_object_or_404(Product, id=product_id)
            if product.quantity < quantity:
                messages.error(request, f"Not enough stock for {product.name}.")
            else:
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=product.selling_price,
                )
                messages.success(request, f"{product.name} added to sale.")

        elif action == "finalize":
            sale = Sale.objects.filter(visit=visit, status='pending').last()
            if not sale:
                messages.error(request, "No items in sale to finalize.")
            else:
                # Total up
                total = sum(item.subtotal() for item in sale.items.all())
                sale.amount = total
                sale.save()

                # Reduce stock
                for item in sale.items.all():
                    item.product.quantity -= item.quantity
                    item.product.save()

                # Create Bill
                Bill.objects.create(
                    visit=visit,
                    patient=patient,
                    description="Pharmacy Sale",
                    amount=total
                )

                visit.stage = "billing_pharmacy"
                visit.save()

                messages.success(request, "Sale finalized and billed.")
                return redirect('view_prescription_note', tracking_code=tracking_code)

    return render(request, "pharmacy/view_prescription_note.html", {
        "visit": visit,
        "patient": patient,
        "prescription": prescription,
        "products": products
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
