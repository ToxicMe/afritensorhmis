from django.db import models
from django.utils import timezone

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    hospital_available = models.ManyToManyField('hospital.Hospital', related_name='available_tests', blank=True)

    def __str__(self):
        return self.name

class TestResult(models.Model):
    visit = models.ForeignKey('registration.Visit', on_delete=models.CASCADE, related_name='test_results')
    patient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='patient_test_results')
    done_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='test_results_done')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Test Results for {self.patient} on {self.created_at.strftime('%Y-%m-%d')}"

class TestResultEntry(models.Model):
    test_result = models.ForeignKey('laboratory.TestResult', on_delete=models.CASCADE, related_name='entries')
    test = models.ForeignKey('laboratory.Test', on_delete=models.CASCADE)
    result = models.TextField()

    def __str__(self):
        return f"{self.test.name} result for {self.test_result.patient}"
