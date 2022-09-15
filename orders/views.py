from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.decorators import http
from django.contrib.auth import decorators as authDecorators

from cart.cart import Cart
from orders import models as orderModels


@authDecorators.login_required
@http.require_GET
def orders(request):
    orders = orderModels.Order.objects.filter(user_id = request.user.id).filter(billing_status = True)
    return render(request, "account/dashboard/orders.html", {"orders": orders})


@http.require_POST
def add(request):
    cart = Cart(request)

    order_key = request.POST.get('order_key')
    cartTotal = cart.get_total_price()

    if orderModels.Order.objects.filter(order_key=order_key).exists():
        pass
    else:
        order = orderModels.Order.objects.create(user_id=request.user.id, full_name='name', address1='add1',
                            address2='add2', total_paid=cartTotal, order_key=order_key)
        orderId = order.pk

        for item in cart:
            orderModels.OrderItem.objects.create(order_id=orderId, product=item['product'], price=item['price'], quantity=item['quantity'])

    response = JsonResponse({'success': 'Order has been set'})
    return response


def orderPaymentConfirmation(data):
    try:
        orderModels.Order.objects.filter(order_key=data).update(billing_status=True)
    except:
        raise Exception("Order cannot be placed")


