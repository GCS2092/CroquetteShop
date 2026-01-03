from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm

# Forms personnalisés
from .forms import SignUpForm, UserProfileForm

# Modèles
from .models import (
    Product,
    DeliveryLocation,
    Order,
    OrderItem,
    Subscription,
    RewardPoint,
    UserProfile
)

# Panier
from .cart import Cart


# =========================
# PAGE D'ACCUEIL
# =========================
def home(request):
    """Page d'accueil avec liste des produits actifs"""
    products = Product.objects.filter(is_active=True)
    return render(request, 'shop/home.html', {'products': products})


# =========================
# PANIER
# =========================
def cart_add(request, product_id):
    """Ajouter un produit au panier"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    messages.success(request, f"{product.name} ajouté au panier !")
    return redirect('cart_detail')


def cart_remove(request, product_id):
    """Retirer un produit du panier"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} retiré du panier.")
    return redirect('cart_detail')


def cart_detail(request):
    """Afficher le panier"""
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


# =========================
# CHECKOUT & COMMANDE
# =========================
def checkout(request):
    """Page de validation de commande"""
    cart = Cart(request)

    # Vérifier que le panier n'est pas vide
    if len(cart) == 0:  # ✅ CORRIGÉ : len(cart) au lieu de len(cart.cart)
        messages.warning(request, "Votre panier est vide !")
        return redirect('home')

    delivery_locations = DeliveryLocation.objects.filter(is_active=True)

    if request.method == 'POST':
        delivery_location_id = request.POST.get('delivery_location')
        notes = request.POST.get('notes', '')

        # Gestion utilisateur connecté ou invité
        if request.user.is_authenticated:
            user = request.user
            guest_name = guest_email = guest_phone = ''
        else:
            user = None
            guest_name = request.POST.get('guest_name', '').strip()
            guest_email = request.POST.get('guest_email', '').strip()
            guest_phone = request.POST.get('guest_phone', '').strip()

            # Validation pour invités
            if not guest_name or not guest_email:
                messages.error(request, "Nom et email sont obligatoires pour les invités.")
                return render(request, 'shop/checkout.html', {
                    'cart': cart,
                    'delivery_locations': delivery_locations
                })

        # Création de la commande
        delivery_location = get_object_or_404(DeliveryLocation, id=delivery_location_id)

        order = Order.objects.create(
            user=user,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            delivery_location=delivery_location,
            total_amount=cart.get_total_price(),
            notes=notes,
            status='pending'  # ✅ CORRIGÉ : 'pending' existe dans ton modèle
        )

        # Ajout des articles
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        # Vider le panier
        cart.clear()

        messages.success(request, f"Commande #{order.id} passée avec succès ! Paiement à la livraison.")
        return redirect('order_success', order_id=order.id)

    return render(request, 'shop/checkout.html', {
        'cart': cart,
        'delivery_locations': delivery_locations
    })


# =========================
# CONFIRMATION COMMANDE
# =========================
def order_success(request, order_id):
    """Page de confirmation de commande"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_success.html', {'order': order})


# =========================
# DÉTAIL D'UNE COMMANDE
# =========================
@login_required
def order_detail(request, order_id):
    """Détail d'une commande (uniquement pour l'utilisateur qui l'a passée)"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})


# =========================
# AUTHENTIFICATION
# =========================
def signup(request):
    """Page d'inscription"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Ajouter le téléphone au profil (créé automatiquement par le signal)
            phone = form.cleaned_data.get('phone')
            if phone:
                user.profile.phone = phone
                user.profile.save()

            # Connexion automatique après inscription
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {username} ! Votre compte a été créé avec succès.")
                return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'shop/signup.html', {'form': form})


def user_login(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {username} !")
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'shop/login.html', {'form': form})


def user_logout(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


# =========================
# PROFIL UTILISATEUR
# =========================
@login_required
def profile(request):
    """Page de profil utilisateur"""
    # Récupérer ou créer les points de fidélité
    reward_points, created = RewardPoint.objects.get_or_create(user=request.user)
    
    # Récupérer les commandes (✅ CORRIGÉ : created_at au lieu de date)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Récupérer les abonnements
    subscriptions = Subscription.objects.filter(user=request.user)

    context = {
        'reward_points': reward_points,
        'orders': orders,
        'subscriptions': subscriptions,
    }
    return render(request, 'shop/profile.html', context)


@login_required
def edit_profile(request):
    """Modifier le profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        phone = request.POST.get('phone', '')
        
        if form.is_valid():
            form.save()
            # Mettre à jour le téléphone dans le profil
            request.user.profile.phone = phone
            request.user.profile.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        # Pré-remplir le téléphone
        form.fields['phone'].initial = request.user.profile.phone

    return render(request, 'shop/edit_profile.html', {'form': form})


# =========================
# PAGE RÉCOMPENSES
# =========================
def rewards(request):
    """Page d'information sur les récompenses"""
    return render(request, 'shop/rewards.html')