from django.db import models
from companies.models import *

# Create your models here.
class Hospital(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='hospitals')

    def __str__(self):
        return self.name