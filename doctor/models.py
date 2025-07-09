from django.db import models
from django.utils import timezone

class DoctorNote(models.Model):
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='doctor_notes')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='patient_doctor_notes')
    doctor_notes = models.TextField()
    tests = models.ManyToManyField('laboratory.Test', blank=True, related_name='doctor_notes')
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='notes_done')

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Doctor Note for {self.patient} by {self.done_by} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class PrescriptionNote(models.Model):
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='patient_prescriptions')
    doctor_prescription = models.TextField()
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions_written')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Prescription for {self.patient} by {self.done_by} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"