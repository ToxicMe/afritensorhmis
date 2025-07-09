from django.urls import path, include

from . import views

urlpatterns = [
    path('register_patient/', views.registration, name='register_patient'),
    path('patients/', views.patient_list, name='patient_list'),
    path('create-visit/', views.create_visit, name='create_visit'),
    path('patient/<int:patient_id>/visits/', views.view_patient_visits, name='view_patient_visits'),
    path('registration_dashboard/', views.registration_dashboard, name='registration_dashboard'),
]