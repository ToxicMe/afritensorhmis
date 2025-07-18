from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

class Visit(models.Model):
    STAGE_CHOICES = [
        ('triage', 'Triage'),
        ('doctor', 'Doctor'),
        ('note', 'Note'),
        ('laboratory', 'Laboratory'),
        ('prescription', 'Prescription'),
        ('billing', 'Billing(From Registration)'),
        ('billing_note', 'Billing (From Note)'),
        ('billing_prescription', 'Billing (From Prescription)'),
        ('billing_pharmacy', 'Billing (From Pharmacy)'),
        ('pharmacy', 'Pharmacy'),
        ('inpatient', 'Inpatient'),
        ('discharged', 'Discharged'),
    ]

    id = models.AutoField(primary_key=True)
    tracking_code = models.CharField(max_length=50, unique=True, editable=True, blank=True, null=True)
    date_time = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)

    hospital = models.ForeignKey('hospital.Hospital', on_delete=models.CASCADE, related_name='visits')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='visits')
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES)

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            random_str = get_random_string(length=6).upper()
            self.tracking_code = f"VIS-{self.hospital.id}-{self.patient.id}-{random_str}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Visit #{self.id} ({self.tracking_code}) - {self.patient} at {self.hospital} on {self.date_time.strftime('%Y-%m-%d %H:%M')}"