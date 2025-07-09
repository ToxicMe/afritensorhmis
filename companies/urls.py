from django.urls import path, include

from . import views

urlpatterns = [
    path('companies/', views.companies, name='companies'),
]