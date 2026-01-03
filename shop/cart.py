from decimal import Decimal
from .models import Product

class Cart:
    """Gestion du panier en session (fonctionne pour invités et connectés)"""
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
    
    def add(self, product, quantity=1):
        """Ajouter un produit au panier"""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        self.cart[product_id]['quantity'] += quantity
        self.save()
    
    def remove(self, product):
        """Retirer un produit du panier"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def update(self, product, quantity):
        """Mettre à jour la quantité d'un produit"""
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity > 0:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.remove(product)
            self.save()
    
    def save(self):
        """Sauvegarder le panier en session"""
        self.session.modified = True
    
    def clear(self):
        """Vider le panier"""
        del self.session['cart']
        self.save()
    
    def __iter__(self):
        """Itérer sur les articles du panier"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        
        for product in products:
            cart[str(product.id)]['product'] = product
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item
    
    def __len__(self):
        """Nombre total d'articles dans le panier"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_total_price(self):
        """Prix total du panier"""
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())