from django_daraja.mpesa.core import MpesaClient

def mpesa_pay(phone_number, amount, account_reference):
    cl = MpesaClient()
    callback_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    transaction_desc = "Hospital Bill"

    return cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
