import json
from django import contrib,  http
from django.shortcuts import render
from django.contrib.auth import decorators
from django.views.decorators import http as httpDecorators
from django.views.generic.base import TemplateView
from account import models as accountModels
from cart.cart import CartProcessor
from orders import models as orderModels
from checkout import models, payment
from cart import exceptions as cartExceptions
import requests


url = 'https://parseapi.back4app.com/classes/City?limit=5&order=-population,name&keys=name,country,countryCode,cityId,objectId'


@decorators.login_required
def deliveryChoices(request):
    deliveryOptions = models.DeliveryOptions.objects.filter(is_active=True)
    if deliveryOptions:
        cart = CartProcessor(request)
        updatedTotalPrice = cart.update_delivery(deliveryType=deliveryOptions[0])
    return render(request, "checkout/delivery_choices.html", {"deliveryOptions": deliveryOptions})


@httpDecorators.require_POST
@decorators.login_required
def cartUpdateDelivery(request):
    try:
        cart = CartProcessor(request)
        deliveryOption = int(request.POST.get("delivery_option"))
        deliveryType = models.DeliveryOptions.objects.get(id=deliveryOption)
        updatedTotalPrice = cart.update_delivery(deliveryType=deliveryType)

        session = request.session
        if "purchase" not in request.session:
            session["purchase"] = {
                "delivery_id": deliveryType.id,
            }
        else:
            session["purchase"]["delivery_id"] = deliveryType.id
            session.modified = True

        return http.JsonResponse({"total": updatedTotalPrice, "delivery_price": deliveryType.delivery_price})
    except models.DeliveryOptions.DoesNotExist:
        return http.HttpResponseNotFound("Delivery option not found")
    except cartExceptions.CartException as err:
        return http.HttpResponseBadRequest(err.message)



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
        contrib.messages.warning(request, "Please select address option")
        return http.HttpResponseRedirect(request.META["HTTP_REFERER"])

    cart = CartProcessor(request)
    total = str(cart.get_total_price)
    total = int(total.replace('.', ''))

    paymentInstance = payment.paymentSystems[payment.PaymentOptions.CARD]
    
    paymentData = paymentInstance.get_or_create_item(userId=request.user.id, data=payment.PaymentData(amount=total, currency="usd", cart_id=cart.cart_id))
    
    cities = json.loads(requests.get(url, headers={
            'X-Parse-Application-Id': 'gJ1k7hOymzwNd0uAzWEquCYG7pI53yGaGwzxRdPi', 
            'X-Parse-Master-Key': '0uAjGdZmuqtoiTpbFTiMj1jpMNmr0lWhREtyyCjM'
        }).content.decode('utf-8'))

    return render(request, 'checkout/payment_selection.html', {"paymentData": paymentData, "paymentOptions": payment.PaymentOptions, "paymentInstance": paymentInstance, "cities":cities["results"], 'cart': cart})


@decorators.login_required
@httpDecorators.require_GET
def paymentSuccessful(request):
    try:
        paymentId = request.GET.get("payment_id", None)
        paymentInstance = payment.paymentSystems[payment.PaymentOptions.CARD]
        if paymentInstance.succeeded(paymentId):
            contrib.messages.success(request, "Payment Successful")
            return render(request, "checkout/payment_successful.html")
        return http.HttpResponseNotFound("Order not found")   
    except orderModels.Order.DoesNotExist:
        return http.HttpResponseNotFound("Order not found")   
    except cartExceptions.CartException as err:
        return http.HttpResponseBadRequest(err.message)        
    
class Error(TemplateView):
    template_name = 'checkout/error.html'
