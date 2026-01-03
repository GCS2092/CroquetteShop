from .cart import Cart

def cart_context(request):
    """Rend le panier disponible dans tous les templates"""
    return {
        'cart': Cart(request)
    }