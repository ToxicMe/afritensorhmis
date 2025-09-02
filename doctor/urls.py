from django.urls import path, include

from . import views

urlpatterns = [
    path('doctor/', views.doctor, name='doctor'),
    path('doctor-visits/', views.doctor_visits_list, name='doctor_visits_list'),
    path('doctor-note/<int:visit_id>/', views.view_doctor_note, name='view_doctor_note'),
    path('doctor-note/<int:visit_id>/add/', views.add_doctor_note, name='add_doctor_note'),
    path('prescription-visits/', views.prescription_visits_list, name='prescription_visits_list'),
    path('prescription/<str:tracking_code>/', views.view_test_results_for_prescription, name='view_prescription_tests'),
    path('prescription/save/<str:tracking_code>/', views.save_prescription_note, name='save_prescription_note'),
    path('doctor/note/add-bill/<int:visit_id>/', views.add_bill_from_note, name='add_bill_from_note'),
    path('billing/unpaid/', views.doctor_unpaid_bills_list, name='doctor_unpaid_bills_list'),
    path('icd10-children/<int:parent_id>/', views.get_icd10_children, name='get_icd10_children'),







]