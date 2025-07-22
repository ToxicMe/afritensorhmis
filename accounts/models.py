from django.contrib.auth.models import AbstractUser
from django.db import models
from hospital.models import *



class InsuranceProvider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="A short internal code like 'jubilee', 'aar'")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    requires_authorization = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class InsuranceInformation(models.Model):
    SCHEME_TYPE_CHOICES = [
        ('inpatient', 'Inpatient'),
        ('outpatient', 'Outpatient'),
        ('in_and_out', 'Inpatient & Outpatient'),
        ('none', 'None'),
    ]

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='insurance_records')

    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='clients',
        limit_choices_to={'is_active': True}  # <-- Only show active providers
    )

    card_number = models.CharField(max_length=50, verbose_name="Card/Membership Number")
    scheme_type = models.CharField(max_length=20, choices=SCHEME_TYPE_CHOICES, verbose_name="Scheme Type")
    principal_name = models.CharField(max_length=100, verbose_name="Principal Member Name")
    relationship_to_principal = models.CharField(max_length=50, verbose_name="Relationship to Principal")

    employer_name = models.CharField(max_length=100, blank=True)
    employer_code = models.CharField(max_length=50, blank=True)

    sha_number = models.CharField(max_length=50, blank=True)
    sha_contribution_proof = models.FileField(upload_to='shif_proofs/', blank=True, null=True)

    pre_authorization_code = models.CharField(max_length=100, blank=True)
    authorization_letter = models.FileField(upload_to='auth_letters/', blank=True, null=True)
    authorization_date = models.DateField(blank=True, null=True)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.insurance_provider.name}"





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
    id_number = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="National ID or Passport Number")
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


