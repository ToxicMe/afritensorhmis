from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Visit)
@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "visit", "referred_to_hospital", "referred_by")
    readonly_fields = ("referred_by",)

    def save_model(self, request, obj, form, change):
        if not obj.referred_by:
            obj.referred_by = request.user
        super().save_model(request, obj, form, change)