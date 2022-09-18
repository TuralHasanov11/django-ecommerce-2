from django.contrib import admin

from orders import models as orderModels

# Register your models here.
@admin.register(orderModels.Order)
class OrderAdmin(admin.ModelAdmin):
  list_display = ("user", "total_paid", "billing_status")
  ordering = ("-created", )