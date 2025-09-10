from django.db import models
from django.utils import timezone

class Triage(models.Model):
    visit = models.ForeignKey(
        'registration.Visit',
        on_delete=models.CASCADE,
        related_name='triages'
    )
    patient = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='triage'
    )
    timestamp = models.DateTimeField(default=timezone.now)

    # Vitals
    bp_sys = models.IntegerField(null=True, blank=True, help_text="Systolic blood pressure (mmHg)")  
    bp_dia = models.IntegerField(null=True, blank=True, help_text="Diastolic blood pressure (mmHg)")
    pr = models.IntegerField(null=True, blank=True, help_text="Pulse rate (bpm)")
    spo2 = models.FloatField(null=True, blank=True, help_text="Oxygen saturation (%)")
    rbs = models.FloatField(null=True, blank=True, help_text="Random blood sugar (mmol/L)")
    temperature = models.FloatField(null=True, blank=True, help_text="Body temperature (°C)")

    # Body measurements
    height = models.FloatField(null=True, blank=True, help_text="Height (cm)")
    weight = models.FloatField(null=True, blank=True, help_text="Weight (kg)")
    bmi = models.FloatField(null=True, blank=True, help_text="Body Mass Index")

    # Advanced body composition (optional if you have smart scale integration)
    #body_fat = models.FloatField(null=True, blank=True, help_text="Body fat percentage (%)")
    #muscle_mass = models.FloatField(null=True, blank=True, help_text="Muscle mass (kg)")
    #bone_mass = models.FloatField(null=True, blank=True, help_text="Bone mass (kg)")
   # metabo_age = models.IntegerField(null=True, blank=True, help_text="Metabolic age")
    #calories = models.IntegerField(null=True, blank=True, help_text="Calories burned per day (kcal)")
    #visce = models.IntegerField(null=True, blank=True, help_text="Visceral fat level")

    recorder_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
        blank=True,
        related_name='triage_recordings'
    )

    def save(self, *args, **kwargs):
        """Auto-calculate BMI before saving"""
        if self.height and self.weight:
            try:
                height_m = float(self.height) / 100  # convert cm → m
                weight_kg = float(self.weight)
                self.bmi = round(weight_kg / (height_m ** 2), 2)
            except (ValueError, TypeError):
                self.bmi = None  # fallback if conversion fails
        super().save(*args, **kwargs)

    @property
    def bmi_category(self):
        """Return BMI category for quick access"""
        if not self.bmi:
            return "N/A"
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 25:
            return "Normal"
        elif 25 <= self.bmi < 30:
            return "Overweight"
        return "Obese"

    def __str__(self):
        return f"Triage for {self.patient} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
