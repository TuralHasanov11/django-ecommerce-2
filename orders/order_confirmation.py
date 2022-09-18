from cart import models as cartModels 
from orders import models as orderModels

def orderPaymentConfirmation(data):
    try:
        order = orderModels.Order.objects.get(order_key=data)
        order.billing_status=True
        order.save(update_fields=['billing_status'])
        cart = cartModels.Cart.objects.get(user=order.user).delete()
        return True
    except:
        raise Exception("Order cannot be placed")
