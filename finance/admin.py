from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Supplier)
admin.site.register(Requisition)
admin.site.register(PurchaseOrderItem)
admin.site.register(PurchaseOrder)
admin.site.register(FixedAsset)
admin.site.register(LedgerEntry)
admin.site.register(CashAccount)
admin.site.register(PettyCashEntry)