from abc import ABC
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Type
from django.conf import settings
from django.views.decorators import csrf
from django import http
from orders.views import orderPaymentConfirmation

# Stripe
import stripe
stripe.api_key: str = settings.STRIPE_ENDPOINT_SECRET


class PaymentIntegrator(ABC):
  pass

@dataclass 
class PaymentData:
  amount: Decimal
  currency: str

@dataclass
class PaymentSystem:
  integrator: Type[PaymentIntegrator]
  credentials: dict


class StripePayment(PaymentIntegrator):

  def get_or_create_item(self, userId: int, data: PaymentData):
    paymentItem = stripe.PaymentIntent.search(query=f"metadata['user_id']:'{userId}'")

    if paymentItem.data:
      paymentItem = paymentItem.data[0]
    else:
      paymentItem = stripe.PaymentIntent.create(
        amount=data.amount,
        currency=data.currency,
        metadata={'user_id': userId}
      )

    return paymentItem

stripeKeys: dict = {
  "endpoint_secret": settings.STRIPE_SECRET_KEY,
  "publishable_key": settings.STRIPE_PUBLISHABLE_KEY
}

class PaymentOptions(Enum):
  CARD: str = "card"

paymentSystems = {
  PaymentOptions.CARD: PaymentSystem(StripePayment, stripeKeys)
}


@csrf.csrf_exempt
def stripeWebhook(request):
    data = request.body
    event = None

    try:
        event = stripe.Webhook.construct_event(
            data, request.headers.get('stripe-signature'), stripeKeys["endpoint_secret"]
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