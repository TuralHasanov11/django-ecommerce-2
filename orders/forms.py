from django import forms

from orders.models import Order

class OrderForm(forms.ModelForm):
    
    class Meta:
        model = Order
        fields = ("full_name", "address1", "address2", "postal_code", "email", "city", "phone", "country_code", "payment_option", "order_key")
