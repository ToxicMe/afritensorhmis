from django.urls import path, include
from . import views

urlpatterns = [
    path('staff_list_view/', views.staff_list_view, name='staff_list_view'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.user_profile, name='user_profile'),
    path('notification/', views.notification, name='notification'),


]