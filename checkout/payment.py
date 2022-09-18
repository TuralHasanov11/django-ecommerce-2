from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from django.conf import settings
from django.views.decorators import csrf
from django import http
from orders import order_confirmation

# Stripe
import stripe

@dataclass 
class PaymentData:
  amount: Decimal
  currency: str
  cart_id: int


class StripePayment:

  def __init__(self) -> None:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    self.endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY

  def get_or_create_item(self, userId: int, data: PaymentData):
    paymentItem = stripe.PaymentIntent.search(query=f"metadata['user_id']:'{userId}' AND status:'requires_payment_method'")

    if paymentItem.data:
      paymentItem = paymentItem.data[0]
    else:
      paymentItem = stripe.PaymentIntent.create(
        amount=data.amount,
        currency=data.currency,
        metadata={'user_id': userId}
      )
    return paymentItem

  def succeeded(self, id: str):
    paymentItem = stripe.PaymentIntent.retrieve(id)
    return paymentItem.status == "succeeded"

class PaymentOptions(Enum):
  CARD: str = "card"

paymentSystems = {
  PaymentOptions.CARD: StripePayment()
}


@csrf.csrf_exempt
def stripeWebhook(request):
    data = request.body
    event = None

    try:
        event = stripe.Webhook.construct_event(
            data, request.headers.get('stripe-signature'), StripePayment().endpoint_secret
        )
    except ValueError as e:
        return http.JsonResponse(status_code=400, content=e)
    except stripe.error.SignatureVerificationError as e:
        return http.JsonResponse(status_code=400, content=e)

    if event['type'] == 'payment_intent.succeeded':
      order_confirmation.orderPaymentConfirmation(event['data']['object']["client_secret"])
    else:
        print('Unhandled event type {}'.format(event['type']))

    return http.HttpResponse(status=200)