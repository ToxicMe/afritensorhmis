from django.urls import path, include

from . import views

urlpatterns = [
    path('register_patient/', views.registration, name='register_patient'),
    path('patients/', views.patient_list, name='patient_list'),
    path('create-visit/', views.create_visit, name='create_visit'),
    path('patient/<int:patient_id>/visits/', views.view_patient_visits, name='view_patient_visits'),
    path('registration_dashboard/', views.registration_dashboard, name='registration_dashboard'),
    path('patients/<int:patient_id>/', views.view_patient, name='view_patient'),
    path('patients/<int:patient_id>/add-insurance/', views.add_insurance_info, name='add_insurance_info'),
    path('visit/<str:tracking_code>/', views.visit_detail, name='visit_detail'),
    path('insurance/remove/<int:insurance_id>/', views.remove_insurance_info, name='remove_insurance_info'),
    path('', views.main_dashboard, name='main_dashboard'),
    path('refferable-visits/', views.refferable_list, name='refferable_visits_list'),
    path("referrals/submit/", views.submit_referral, name="submit_referral"),




]