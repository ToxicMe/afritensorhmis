from django.db import models
from django.utils import timezone

class ICD10Entry(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    label = models.TextField()
    kind = models.CharField(max_length=20)  # chapter, block, category, subcategory
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    def __str__(self):
        return f"{self.code} - {self.label}"

class DoctorNote(models.Model):
    visit = models.ForeignKey(
        'registration.Visit',
        on_delete=models.CASCADE,
        related_name='doctor_notes'
    )
    patient = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='patient_doctor_notes'
    )
    doctor_notes = models.TextField()
    tests = models.ManyToManyField(
        'laboratory.Test',
        blank=True,
        related_name='doctor_notes'
    )
    icd10_codes = models.ManyToManyField(
        'doctor.ICD10Entry',
        blank=True,
        related_name='doctor_notes',
        help_text="Select one or more ICD-10 codes (any level: chapter, block, category, subcategory)."
    )
    done_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_done'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        icd_codes = ", ".join([c.code for c in self.icd10_codes.all()])
        return f"Doctor Note for {self.patient} by {self.done_by} on {self.created_at.strftime('%Y-%m-%d %H:%M')} | ICD-10: {icd_codes}"

        

class PrescriptionNote(models.Model):
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='patient_prescriptions')
    doctor_prescription = models.TextField()
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions_written')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Prescription for {self.patient} by {self.done_by} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"