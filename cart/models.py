from django.db import models

from store import models as productModels 
from account import models as accountModels


class Cart:
    user = models.ForeignKey(accountModels.Account, null=False, blank=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "created_at"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, null=False, blank=False, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(productModels.Product, null=False, blank=False, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=False, blank=False)

