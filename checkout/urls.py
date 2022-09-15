from django.urls import path

from checkout import views

app_name = "checkout"

urlpatterns = [
    path("delivery-choices/", views.deliveryChoices, name="delivery_choices"),
    path("cart-update-delivery/", views.cartUpdateDelivery, name="cart_update_delivery"),
    path("delivery-address/", views.deliveryAddress, name="delivery_address"),
    path("payment-selection/", views.paymentSelection, name="payment_selection"),
    path("payment-successful/", views.paymentSuccessful, name="payment_successful"),
    path('webhook/', views.stripeWebhook, name="payment_webhook"),

]