from django.contrib import messages, auth
from django.http import  HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django import urls, dispatch
from django.utils import http, encoding
from django.views.decorators import http
from django.db.models import signals

from orders import models as orderModels
from store import models as storeModels
from account import forms, models as accountModels, tokens, activation as activationMethods

@http.require_GET
@auth.decorators.login_required
def dashboard(request):
    orders = orderModels.Order.objects.prefetch_related("items").filter(user_id=request.user.id).filter(billing_status=True)
    return render(request,
                  'account/user/dashboard.html',
                  {'section': 'profile', 'orders': orders})

@http.require_http_methods(["POST", "GET"])
def register(request):

    if request.user.is_authenticated:
        return redirect('account:dashboard')

    if request.method == 'POST':
        registerForm = forms.RegistrationForm(request.POST)
        if registerForm.is_valid():
            user = registerForm.save(commit=False)
            user.email = registerForm.cleaned_data['email']
            user.set_password(registerForm.cleaned_data['password'])
            user.is_active = False
            user.save()
            return render(request, "account/auth/register_email_confirm.html")
    else:
        registerForm = forms.RegistrationForm()
    return render(request, 'account/auth/register.html', {'form': registerForm})


@dispatch.receiver(signals.post_save, sender=accountModels.Account)
def accountPostRegistered(sender, instance, created, **kwargs):
    if created:
        activationMethods.sendEmailConfirmation(user=instance)


@http.require_http_methods(["POST", "GET"])
@auth.decorators.login_required
def edit(request):
    if request.method == 'POST':
        user_form = forms.UserEditForm(instance=request.user, data=request.POST)

        if user_form.is_valid():
            user_form.save()
    else:
        user_form = forms.UserEditForm(instance=request.user)

    return render(request,
                  'account/user/edit.html', {'user_form': user_form})

@http.require_POST
@auth.decorators.login_required
def delete(request):
    user = accountModels.Account.objects.get(user_name=request.user)
    user.is_active = False
    user.save()
    auth.logout(request)
    return redirect('account:delete_confirmation')


@http.require_GET
def activate(request, uidb64, token):
    try:
        uid = encoding.force_str(http.urlsafe_base64_decode(uidb64))
        user = accountModels.Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, accountModels.Account.DoesNotExist):
        user = None
    if user and tokens.account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        auth.login(request, user)
        return redirect('account:dashboard')
    else:
        return render(request, 'account/auth/activation_invalid.html')


@auth.decorators.login_required
def addresses(request):
    addresses = accountModels.Address.objects.filter(account=request.user)
    return render(request, "account/user/addresses.html", {"addresses": addresses})


@auth.decorators.login_required
@http.require_http_methods(["GET", "POST"])
def addAddress(request):
    if request.method == "POST":
        address_form = forms.UserAddressForm(data=request.POST)
        if address_form.is_valid():
            address_form = address_form.save(commit=False)
            address_form.account = request.user
            address_form.save()
            return HttpResponseRedirect(urls.reverse("account:addresses"))
    else:
        address_form = forms.UserAddressForm()
    return render(request, "account/user/edit_addresses.html", {"form": address_form})


@auth.decorators.login_required
@http.require_http_methods(["GET", "POST"])
def editAddress(request, id):
    if request.method == "POST":
        address = accountModels.Address.objects.get(pk=id, account=request.user)
        address_form = forms.UserAddressForm(instance=address, data=request.POST)
        if address_form.is_valid():
            address_form.save()
            return HttpResponseRedirect(urls.reverse("account:addresses"))
    else:
        address = accountModels.Address.objects.get(pk=id, account=request.user)
        address_form = forms.UserAddressForm(instance=address)
    return render(request, "account/user/edit_addresses.html", {"form": address_form})


@auth.decorators.login_required
def deleteAddress(request, id):
    accountModels.Address.objects.filter(pk=id, account=request.user).delete()
    return redirect("account:addresses")


@auth.decorators.login_required
def setDefaultAddress(request, id):
    accountModels.Address.objects.filter(account=request.user, default=True).update(default=False)
    accountModels.Address.objects.filter(pk=id, account=request.user).update(default=True)

    previous_url = request.META.get("HTTP_REFERER")

    if "delivery_address" in previous_url:
        return redirect("checkout:delivery_address")

    return redirect("account:addresses")


@auth.decorators.login_required
def wishlist(request):
    products = storeModels.Product.products.filter(user_wishlist=request.user)
    return render(request, "account/user/wishlist.html", {"wishlist": products})


@auth.decorators.login_required
def addToWishlist(request, id):
    product = get_object_or_404(storeModels.Product, id=id)
    if product.user_wishlist.filter(id=request.user.id).exists():
        product.user_wishlist.remove(request.user)
        messages.success(request, product.title + " has been removed from your WishList")
    else:
        product.user_wishlist.add(request.user)
        messages.success(request, "Added " + product.title + " to your WishList")
    return HttpResponseRedirect(request.META["HTTP_REFERER"])
