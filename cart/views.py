from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators import http as httpDecorators

from cart.cart import CartProcessor
from cart import exceptions
from store import models


def cart(request):
    cart = CartProcessor(request)
    return render(request, 'cart/summary.html', {'cart': cart}) 


@httpDecorators.require_POST
def cartAdd(request):
    try:
        cart = CartProcessor(request) 

        productId = int(request.POST.get('product_id'))
        productQuantity = int(request.POST.get('product_quantity'))
        product = get_object_or_404(models.Product, id= productId)
        cart.create(product= product, quantity= productQuantity)
        
        return JsonResponse({'quantity': cart.__len__()})
    except exceptions.CartException as err:
        return HttpResponseBadRequest(err.message)
        

@httpDecorators.require_POST
def cartDelete(request):
    try:
        cart = CartProcessor(request)
        productId = int(request.POST.get('product_id'))
        cart.delete(product= productId)

        return JsonResponse({'quantity': cart.__len__(), 'subtotal': cart.get_total_price}) 
    except exceptions.CartException as err:
        return HttpResponseBadRequest(err.message)


@httpDecorators.require_POST
def cartUpdate(request):
    try:
        cart = CartProcessor(request)
        productId = int(request.POST.get('product_id'))
        productQuantity = int(request.POST.get('product_quantity'))
        cart.update(productId= productId, quantity= productQuantity)

        return JsonResponse({'quantity': cart.__len__(), 'subtotal': cart.get_total_price}) 
    except exceptions.CartException as err:
        return HttpResponseBadRequest(err.message)  
