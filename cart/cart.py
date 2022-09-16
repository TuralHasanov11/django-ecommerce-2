from decimal import Decimal
from django.conf import settings
from cart import models as cartModels, exceptions
from checkout import models as checkoutModels
from store import models as productModels


class CartProcessor:
    def __init__(self, request):
        self.session = request.session
        cart_id = self.session.get(settings.CART_SESSION_ID)

        if settings.CART_SESSION_ID in request.session:
            try:
                cart, created = cartModels.Cart.objects.prefetch_related("cart_items__product").get_or_create(user=request.user)
                cart_id = self.session[settings.CART_SESSION_ID] = cart.id
            except cartModels.Cart.DoesNotExist:
                cart = {}
                cart_id = self.session[settings.CART_SESSION_ID] = ""
        else:
            cart_id = self.session[settings.CART_SESSION_ID] = ""
            cart = {}

        self.cart = {}
        self.cart_id = cart_id
        self.products = []
        if cart.cart_items:
            cartItems = list(cart.cart_items.all())
            for item in cartItems:
                self.cart[str(item.product.id)] = {'price': str(item.product.regular_price), 'quantity': item.quantity}
            self.products = [item.product for item in cartItems]
        self.save()


    def __iter__(self):
        
        cart = self.cart.copy()
        for product in self.products:
            cart[str(product.id)]['product'] = product
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    # number of items in cart
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    @property
    def get_delivery_option(self):
        if "purchase" in self.session:
            return self.session["purchase"]["delivery_id"]
        return 0

    @property
    def get_delivery_price(self) -> Decimal:
        newPrice = 0.00

        if "purchase" in self.session:
            newPrice = checkoutModels.DeliveryOptions.objects.get(id=self.session["purchase"]["delivery_id"]).delivery_price
        return newPrice  
    
    @property
    def get_subtotal_price(self) -> Decimal:
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    @property
    def get_total_price(self) -> Decimal:
        return self.get_subtotal_price + Decimal(self.get_delivery_price)


    def create(self, product: productModels.Product, quantity: int):
        productId = str(product.id)
        try:            
            if not productId in self.cart:
                cartModels.CartItem.objects.create(cart_id=self.cart_id, product=product, quantity=quantity)
                self.cart[productId] = {'price': str(product.regular_price), 'quantity': quantity}
                
            self.save()
        except Exception as err:
            raise exceptions.CartException("Product cannot be added or modified in Shopping cart")

    def update(self, productId: int, quantity: int):
        productId = str(productId)
        try:            
            if productId in self.cart:
                cartModels.CartItem.objects.filter(cart_id=self.cart_id, product_id=productId).update(quantity=quantity)
                self.cart[productId]['quantity'] = quantity

            self.save()
        except Exception as err:
            raise exceptions.CartException("Product cannot be added or modified in Shopping cart")


    def update_delivery(self, deliveryType: checkoutModels.DeliveryOptions):
        total = self.get_subtotal_price + deliveryType.delivery_price
        return total


    def delete(self, product: productModels.Product) -> None:
        productId = str(product)

        try:
            productId = str(product.id)

            if productId in self.cart:
                cartModels.CartItem.objects.filter(cart=self.cart_id, product=product).delete()
                del self.cart[productId]
                self.save()
        except:
            raise exceptions.CartException("Product is not added to Shopping cart")


    def clear(self) -> None:
        try:
            cartModels.Cart.objects.get(id=self.cart_id).delete()
            del self.session["address"]
            del self.session["purchase"]
            del self.session[settings.CART_SESSION_ID]
            self.save()
        except:
            raise exceptions.CartException("Shopping cart cannot be cleared")


    def save(self) -> None:
        self.session.modified = True
                


