from django.urls import path, include

from . import views

urlpatterns = [
    path('pharmacy/', views.pharmacy, name='pharmacy'),
    path('pharmacy/visits/', views.pharmacy_visits_list, name='pharmacy_visits_list'),
    path('pharmacy/visit/<str:tracking_code>/prescription/', views.view_prescription_note, name='view_prescription_note'),
    path('products/add/', views.add_product, name='add_product'),
    path('sale/add/<str:tracking_code>/', views.add_sale_from_prescription, name='add_sale_from_prescription'),



]