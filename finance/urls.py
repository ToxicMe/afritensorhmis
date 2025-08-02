from django.urls import path, include

from . import views

urlpatterns = [
        path('accounting/', views.accounting, name='accounting'), 
        path('cash_flow/', views.cash_flow, name='cash_flow'),
        path('fixed_assets/', views.fixed_assets, name='fixed_assets'), 
        path('receivables/', views.receivables, name='receivables'), 
        path('trial_balance/', views.trial_balance, name='trial_balance'),     
        path('receivables/details/<int:bill_id>/', views.receivables_details, name='receivables_details'),
        path('payables/', views.payables, name='payables'),
        path('balance_sheet/', views.balance_sheet, name='balance_sheet'),
        path('general_ledger/', views.general_ledger, name='general_ledger'),      
        path('payables/details/', views.payables_details, name='payables_details'),
        path('cash_management/', views.cash_management, name='cash_management'),
        path('moh_dashboard/', views.moh_dashboard, name='moh_dashboard'),
        path('outpatient_register/', views.outpatient_register, name='outpatient_register'),
        path('xray_register/', views.xray_register, name='xray_register'),
        path('laboratory_register/', views.laboratory_register, name='laboratory_register'),
        path('inpatient_register/', views.inpatient_register, name='inpatient_register'),
        path('preart_register/', views.preart_register, name='preart_register'),
        path('art_register/', views.art_register, name='art_register'),
        path('htc_lab_register/', views.htc_lab_register, name='htc_lab_register'),
        path('maternity_register/', views.maternity_register, name='maternity_register'),
        path('preart_care_register/', views.preart_care_register, name='preart_care_register'),
        path('sgbv_register/', views.sgbv_register, name='sgbv_register'),
        path('daily_activity_register/', views.daily_activity_register, name='daily_activity_register'),
        path('suppliers/', views.supplier_list, name='supplier_list'),
        path('suppliers/add/', views.add_supplier, name='add_supplier'),
        path('requisitions/', views.requisition_list, name='requisition_list'),
        path('requisitions/create/', views.requisition_create, name='requisition_create'),
        path('requisitions/<int:pk>/', views.requisition_detail, name='requisition_detail'),
        path('requisitions/<int:pk>/approve/', views.approve_requisition, name='approve_requisition'),
        path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
        path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
        path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
        path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
        path('assets/add/', views.add_fixed_asset, name='add_fixed_asset'),
        path('income_statement', views.income_statement, name='income_statement'),
        path('payments', views.payments, name='payments'),
        path('petty_cash', views.petty_cash, name='petty_cash'),
        path("petty-cash/add/", views.add_petty_cash_entry, name="add_petty_cash_entry"),
        path('petty-cash/<int:entry_id>/', views.view_petty_cash_entry, name='view_petty_cash_entry'),






    







]