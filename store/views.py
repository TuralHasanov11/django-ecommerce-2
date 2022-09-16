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
        category__in=models.Category.objects.get(name=category_slug).get_descendants(include_self=True)
    )
    return render(request, 'store/category.html', {'category': category, 'products': products})

@http.require_GET
def productDetail(request, slug):
    try:
        product = models.Product.products.prefetch_related('product_image').get(slug=slug)
        return render(request, 'store/detail.html', {'product': product})
    except models.Product.DoesNotExist:
        return HttpResponseNotFound("Product not found")
    