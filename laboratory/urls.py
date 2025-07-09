from django.urls import path, include

from . import views

urlpatterns = [
    path('laboratory/', views.laboratory, name='laboratory'),
    path('laboratory-visits/', views.lab_visits_list, name='laboratory_visits_list'),
    path('all-tests/', views.all_tests_list, name='all_tests_list'),
    path('submit-findings/<int:note_id>/', views.submit_test_findings, name='submit_test_findings'),



]