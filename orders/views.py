import json
from django.http.response import JsonResponse, HttpResponseBadRequest
from django.views.decorators import http
from django.contrib.auth import decorators as authDecorators

from cart.cart import CartProcessor
from checkout import payment
from orders import models as orderModels,  forms as orderForms

@authDecorators.login_required
@http.require_POST
def add(request):
     
    form = orderForms.OrderForm(request.POST) 
    
    if form.is_valid():
        
        cart = CartProcessor(request)
        data = form.cleaned_data

        cartTotal = cart.get_total_price
        try:
            if not orderModels.Order.objects.filter(order_key=data["order_key"]).exists():
                order = orderModels.Order.objects.create(
                    user=request.user, 
                    full_name=data["full_name"], 
                    address1=data["address1"], 
                    address2=data["address2"], 
                    total_paid=cartTotal, 
                    order_key=data["order_key"],
                    email=data["email"] or request.user.email,
                    city=data["city"],
                    phone=data["phone"],
                    postal_code=data["postal_code"],
                    country_code=data["country_code"],
                    payment_option=payment.PaymentOptions.CARD,
                )

                for item in cart:
                    orderModels.OrderItem.objects.create(order_id=order.id, product=item['product'], price=item['price'], quantity=item['quantity'])

                return JsonResponse({"order_id": order.id})
        except Exception as err:
            print(err)
            return HttpResponseBadRequest(json.dumps(err)) 
        return JsonResponse({'success': 'Order has been set'})
    else:
        return JsonResponse(form.errors, status=400) 




