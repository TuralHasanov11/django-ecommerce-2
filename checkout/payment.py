from dataclasses import dataclass
from enum import Enum
from typing import Protocol

# Stripe
import stripe

@dataclass
class StripePayment:

  userId: int
  currency: str
  amount: int

  def create(self) -> stripe.PaymentIntent:
    self.paymentItem = stripe.PaymentIntent.create(
        amount=self.amount,
        currency=self.currency,
        metadata={'userid': self.userId}
    )

  def search(self, param, value) -> stripe.PaymentIntent:
    self.paymentItem = stripe.PaymentIntent.search(query=f"client_secret:'{value}'")



class PaymentOptions(Enum):
  CARD: str = StripePayment
