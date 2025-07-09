from django.urls import path, include

from . import views

urlpatterns = [
    path('triage/', views.triage, name='triage'),
    path('triage/create/<int:visit_id>/', views.create_triage, name='create_triage'),
    path('triage-visits/', views.triage_visits_list, name='triage_visits_list'),

]