from django.urls import path, include

from . import views

urlpatterns = [
        path('billing/', views.billing, name='billing'),
        path('unpaid_bills/', views.unpaid_bills_list, name='unpaid_bills_list'),
        path('billing/view/<str:transaction_id>/', views.view_bill, name='view_bill'),
        path('<str:tracking_code>/mark-paid/', views.mark_bills_paid, name='mark_bills_paid'),
        path('mpesa-pay/', views.mpesa_pay, name='mpesa_pay'),


    

]