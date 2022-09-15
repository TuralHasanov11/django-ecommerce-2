from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators import http as httpDecorators

from cart.cart import Cart
from store import models


def cart(request):
    cart = Cart(request)
    return render(request, 'cart/summary.html', {'cart': cart}) 

@httpDecorators.require_POST
def cartAdd(request):
    cart = Cart(request) 

    productId = int(request.POST.get('product_id'))
    productQuantity = int(request.POST.get('product_quantity'))
    product = get_object_or_404(models.Product, id= productId)
    cart.add(product= product, quantity= productQuantity)

    cartQuantity = cart.__len__()
    
    return JsonResponse({'quantity': cartQuantity})

@httpDecorators.require_POST
def cartDelete(request):
    cart = Cart(request)
    productId = int(request.POST.get('product_id'))
    cart.delete(product= productId)

    cartQuantity = cart.__len__()
    cartTotal = cart.get_total_price()

    return JsonResponse({'quantity': cartQuantity, 'subtotal': cartTotal})

@httpDecorators.require_POST
def cartUpdate(request):
    cart = Cart(request)
    productId = int(request.POST.get('product_id'))
    productQuantity = int(request.POST.get('product_quantity'))
    cart.update(product= productId, quantity= productQuantity)

    cartQuantity = cart.__len__()
    cartTotal = cart.get_total_price()

    return JsonResponse({'quantity': cartQuantity, 'subtotal': cartTotal})    
