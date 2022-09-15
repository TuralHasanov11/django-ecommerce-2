import json
from locale import currency
import os
from django import contrib,  http
from django.shortcuts import render
from django.contrib.auth import decorators
from django.views.decorators import csrf, http as httpDecorators
from django.conf import settings
from django.views.generic.base import TemplateView
from account import models as accountModels
from cart.cart import Cart
from orders import models as orderModels
from checkout import models, payment
from orders.views import orderPaymentConfirmation
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_ENDPOINT_SECRET


@decorators.login_required
def deliveryChoices(request):
    deliveryOptions = models.DeliveryOptions.objects.filter(is_active=True)
    return render(request, "checkout/delivery_choices.html", {"deliveryOptions": deliveryOptions})


@httpDecorators.require_POST
@decorators.login_required
def cartUpdateDelivery(request):
    cart = Cart(request)
    deliveryOption = int(request.POST.get("delivery_option"))
    deliveryType = models.DeliveryOptions.objects.get(id=deliveryOption)
    updatedTotalPrice = cart.cart_update_delivery(deliveryType.delivery_price)

    session = request.session
    if "purchase" not in request.session:
        session["purchase"] = {
            "delivery_id": deliveryType.id,
        }
    else:
        session["purchase"]["delivery_id"] = deliveryType.id
        session.modified = True

    response = http.JsonResponse({"total": updatedTotalPrice, "delivery_price": deliveryType.delivery_price})
    return response


@decorators.login_required
def deliveryAddress(request):

    session = request.session
    if "purchase" not in request.session:
        contrib.messages.success(request, "Please select delivery option")
        return http.HttpResponseRedirect(request.META["HTTP_REFERER"])

    addresses = accountModels.Address.objects.filter(account=request.user).order_by("-default")

    if "address" not in request.session:
        session["address"] = {"address_id": str(addresses[0].id)}
    else:
        session["address"]["address_id"] = str(addresses[0].id)
        session.modified = True

    return render(request, "checkout/delivery_address.html", {"addresses": addresses})


@decorators.login_required
def paymentSelection(request):

    if "address" not in request.session:
        contrib.messages.success(request, "Please select address option")
        return http.HttpResponseRedirect(request.META["HTTP_REFERER"])

    return render(request, "checkout/payment_selection.html", {})


@decorators.login_required
def paymentSuccessful(request):
    try:
        orders = orderModels.Order.objects.filter(user_id = request.user.id).filter(billing_status = True)    
        cart = Cart(request)
        cart.clear()
        return render(request, "checkout/payment_successful.html", {})
    except orderModels.Order.DoesNotExist:
        return http.HttpResponseNotFound()         
    


class Error(TemplateView):
    template_name = 'checkout/error.html'


@decorators.login_required
def cartView(request):

    cart = Cart(request)
    total = str(cart.get_total_price())
    total = int(total.replace('.', ''))

    order = orderModels.Order.objects.filter(billing_status=False).filter(user=request.user)
    paymentSystem = payment.PaymentOptions.CARD

    paymentInstance = paymentSystem(userId=request.user.id, amount=total, currency="str")

    if order:
        paymentInstance.search(param="client_secret", value=order[0].order_key)
        if not paymentInstance.paymentItem:
            paymentInstance.create()
    else:
        paymentInstance.create()

    result = paymentInstance.paymentItem


    return render(request, 'checkout/payment_selection.html', result)


@csrf.csrf_exempt
def stripeWebhook(request):
    data = request.body
    event = None

    try:
        event = stripe.Webhook.construct_event(
            data, request.headers.get('stripe-signature'), endpoint_secret
        )
    except ValueError as e:
        return http.JsonResponse(status_code=400, content=e)
    except stripe.error.SignatureVerificationError as e:
        return http.JsonResponse(status_code=400, content=e)

    if event.type == 'payment_intent.succeeded':
        orderPaymentConfirmation(event.data.object.client_secret)
    else:
        print('Unhandled event type {}'.format(event.type))

    return http.HttpResponse(status=200)