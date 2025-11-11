from django.urls import path, include

from . import views

urlpatterns = [
    path('ward/', views.ward_dashboard, name='ward_dashboard'),
    path('ward-visits/', views.ward_visits_list, name='ward_visits_list'),
]