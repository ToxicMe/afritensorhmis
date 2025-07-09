from django.db import models
from django.utils import timezone

class Triage(models.Model):
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='triages')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='triages')
    timestamp = models.DateTimeField(default=timezone.now)

    bp_dia = models.IntegerField(null=True, blank=True, help_text="Diastolic blood pressure (mmHg)")
    bp = models.IntegerField(null=True, blank=True, help_text="Systolic blood pressure (mmHg)")
    pr = models.IntegerField(null=True, blank=True, help_text="Pulse rate (bpm)")
    spo2 = models.FloatField(null=True, blank=True, help_text="Oxygen saturation (%)")
    rbs = models.FloatField(null=True, blank=True, help_text="Random blood sugar (mmol/L)")
    temperature = models.FloatField(null=True, blank=True, help_text="Body temperature (°C)")
    
    height = models.FloatField(null=True, blank=True, help_text="Height (cm)")
    weight = models.FloatField(null=True, blank=True, help_text="Weight (kg)")
    bmi = models.FloatField(null=True, blank=True, help_text="Body Mass Index")
    body_fat = models.FloatField(null=True, blank=True, help_text="Body fat percentage (%)")
    muscle_mass = models.FloatField(null=True, blank=True, help_text="Muscle mass (kg)")
    bone_mass = models.FloatField(null=True, blank=True, help_text="Bone mass (kg)")
    metabo_age = models.IntegerField(null=True, blank=True, help_text="Metabolic age")
    calories = models.IntegerField(null=True, blank=True, help_text="Calories burned per day (kcal)")
    visce = models.IntegerField(null=True, blank=True, help_text="Visceral fat level")

    recorder_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, editable=False, blank=True, related_name='triage_recordings')

    def __str__(self):
        return f"Triage for {self.patient} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
