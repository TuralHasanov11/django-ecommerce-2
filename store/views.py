from django.shortcuts import get_object_or_404, render
from django.views.decorators import http
from django.http import HttpResponseNotFound
from store import models


@http.require_GET
def products(request):
    products = models.Product.products.prefetch_related('product_image').all()
    return render(request, 'store/index.html', {'products': products})

@http.require_GET
def categoryProducts(request, category_slug=None):
    category = get_object_or_404(models.Category, slug=category_slug)
    products = models.Product.products.prefetch_related('product_image').filter(
        category=models.Category.objects.get(slug=category_slug)
    )
    return render(request, 'store/category.html', {'category': category, 'products': products})

@http.require_GET
def productDetail(request, slug):
    try:
        product = models.Product.products.select_related('product_type','category').prefetch_related('product_image', 'product_specification_value').get(slug=slug)
        
        if request.user.is_authenticated:
            wishlist = [item.id for item in models.Product.products.filter(user_wishlist=request.user)]
        else:
            wishlist = []
        return render(request, 'store/detail.html', {'product': product, 'wishlist':wishlist})
    except models.Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")
    