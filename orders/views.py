from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.decorators import http
from django.contrib.auth import decorators as authDecorators

from cart.cart import CartProcessor
from orders import models as orderModels


@authDecorators.login_required
@http.require_GET
def orders(request):
    orders = orderModels.Order.objects.filter(user_id = request.user.id).filter(billing_status = True)
    return render(request, "account/dashboard/orders.html", {"orders": orders})


@http.require_POST
def add(request):
    cart = CartProcessor(request)

    order_key = request.POST.get('order_key')
    cartTotal = cart.get_total_price

    if not orderModels.Order.objects.filter(order_key=order_key).exists():
        order = orderModels.Order.objects.create(
            user=request.user, 
            full_name='name', 
            address1='add1', 
            address2='add2', 
            total_paid=cartTotal, 
            order_key=order_key
        )

        for item in cart:
            orderModels.OrderItem.objects.create(order_id=order.id, product=item['product'], price=item['price'], quantity=item['quantity'])
        
    return JsonResponse({'success': 'Order has been set'})


def orderPaymentConfirmation(data):
    try:
        orderModels.Order.objects.filter(order_key=data).update(billing_status=True)
    except:
        raise Exception("Order cannot be placed")


