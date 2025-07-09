from django.contrib.auth.models import AbstractUser
from django.db import models
from hospital.models import *


class CustomUser(AbstractUser):
    hospital = models.ForeignKey('hospital.Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    patient_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)  # Override default email
    account_type = models.CharField(max_length=100, choices=[
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
    ])
    date_of_registration = models.DateField(auto_now_add=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    nationality = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    residence = models.CharField(max_length=255, blank=True, null=True)
    town = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    father_name = models.CharField(max_length=255, blank=True, null=True)

    next_of_kin_name = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_residential_address = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_phone_number = models.CharField(max_length=20, blank=True, null=True)
    next_of_kin_email = models.EmailField(blank=True, null=True)
    next_of_kin_relationship = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Keep username for compatibility unless you remove it

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


