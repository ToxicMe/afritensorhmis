from django.db import models
from hospital.models import Hospital
from django.db.models.signals import post_migrate
from django.dispatch import receiver




class WardCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Ward(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    categories = models.ManyToManyField(WardCategory)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ward in {self.hospital.name}"


# ✅ Category List
WARD_CATEGORIES = [
    "Emergency / Trauma Ward",
    "Medical Ward",
    "Surgical Ward",
    "Maternity / Maternal Ward",
    "Paediatric Ward",
    "Orthopedic Ward",
    "Psychiatric Ward",
    "Oncology Ward",
    "Cardiology Ward",
    "Ophthalmology Ward",
    "ENT Ward",
    "Burns Ward",
    "Geriatric Ward",
    "Intensive Care Unit (ICU)",
    "High Dependency Unit (HDU)",
    "General Ward",
    "Rehabilitation Ward",
    "Post-Anesthesia Care Unit (PACU)",
    "Neonatal Intensive Care Unit (NICU)",
    "Ambulatory Surgery Unit",
]


# ✅ Automatically create WardCategory entries after migration
@receiver(post_migrate)
def create_default_ward_categories(sender, **kwargs):
    if sender.name == __name__.rsplit('.', 1)[0]:  # Ensure only runs for this app
        for category in WARD_CATEGORIES:
            WardCategory.objects.get_or_create(name=category)
