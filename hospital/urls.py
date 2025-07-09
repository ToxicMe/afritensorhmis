from django.urls import path, include

from . import views

urlpatterns = [
    path('hospital/', views.hospital, name='hospital'),
]