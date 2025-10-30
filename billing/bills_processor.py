from billing.models import Bill  # adjust the import based on your app name
from registration.models import Visit
from accounts.models import CustomUser
from django.utils import timezone
from decimal import Decimal
from django.http import HttpResponse
from django_daraja.mpesa.core import MpesaClient

def normalize_phone_number(phone_number: str) -> str:
    """Convert phone number into Safaricom's required format 2547XXXXXXXX."""
    phone_number = phone_number.strip().replace(" ", "")
    
    if phone_number.startswith("+"):
        phone_number = phone_number[1:]  # remove leading +
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    
    return phone_number

def mpesa_pay(phone_number, amount, account_reference="REF123", transaction_desc="Payment"):
    """
    Triggers an M-Pesa STK Push Prompt to the customer's phone.
    """
    cl = MpesaClient()
    callback_url = "https://api.darajambili.com/express-payment"  # Replace with your callback endpoint

     # normalize
    phone_number = normalize_phone_number(phone_number)
    amount = int(amount)  # ensure integer

    response = cl.stk_push(
        phone_number,
        amount,
        account_reference,
        transaction_desc,
        callback_url
    )
    return response 




def create_bill(visit_id, patient_id, description, amount, payment_method=None):
    try:
        visit = Visit.objects.get(id=visit_id)
        patient = CustomUser.objects.get(id=patient_id)

        bill = Bill.objects.create(
            visit=visit,
            patient=patient,
            description=description,
            amount=Decimal(amount),
            date=timezone.now(),
            payment_method=payment_method  # optional
            # status will be set to "pending" automatically
        )

        return bill

    except Visit.DoesNotExist:
        return f"Visit with id {visit_id} not found."
    except CustomUser.DoesNotExist:
        return f"Patient with id {patient_id} not found."
    except Exception as e:
        return f"Error: {str(e)}"
