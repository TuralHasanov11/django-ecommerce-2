from django.contrib import admin
from cart import models as cartModels

@admin.register(cartModels.Cart)
class CartAdmin(admin.ModelAdmin):
  list_display = ("user", )
  ordering = ("-created_at", )


