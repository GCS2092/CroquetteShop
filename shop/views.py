from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
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
    UserProfile,
    Notification,
    Conversation,
    Message
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


@login_required
def order_chat(request, order_id):
    """Vue de chat liée à une commande. Accessible par le client propriétaire ou le staff (admin)."""
    order = get_object_or_404(Order, id=order_id)

    # Permission: owner or staff
    if not (order.user == request.user or request.user.is_staff):
        messages.error(request, "Vous n'êtes pas autorisé à accéder à cette discussion.")
        return redirect('profile')

    # Récupérer la conversation si elle existe
    conversation = order.conversations.first()
    messages_qs = conversation.messages.all() if conversation else []

    return render(request, 'shop/order_chat.html', {
        'order': order,
        'conversation': conversation,
        'messages': messages_qs
    })


@login_required
def notifications(request):
    """Page listant les notifications de l'utilisateur"""
    notes = request.user.notifications.all().order_by('-created_at')
    # Do not auto-mark here anymore; let user mark read explicitly in the UI
    return render(request, 'shop/notifications.html', {'notifications': notes})

from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read via AJAX"""
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.unread = False
    notif.save()
    unread = request.user.notifications.filter(unread=True).count()
    return JsonResponse({'ok': True, 'unread': unread})

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(unread=True).update(unread=False)
    return JsonResponse({'ok': True, 'unread': 0})

@staff_member_required
def admin_messages_list(request):
    """List conversations relevant to staff with unread counts"""
    qs = Conversation.objects.all().order_by('-created_at')
    if not request.user.is_superuser:
        qs = qs.filter(participants=request.user)

    conversations = []
    for c in qs:
        unread = c.messages.filter(read=False).exclude(sender=request.user).count()
        last = c.messages.last()
        conversations.append({'conv': c, 'unread': unread, 'last': last})

    return render(request, 'shop/admin_messages_list.html', {'conversations': conversations})

@staff_member_required
def admin_message_detail(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    if not request.user.is_superuser and request.user not in conv.participants.all():
        messages.error(request, "Vous n'êtes pas autorisé à voir cette conversation.")
        return redirect('admin_messages_list')

    order = conv.order

    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            msg = Message.objects.create(conversation=conv, sender=request.user, content=content)
            # Create notifications for other participants
            for p in conv.participants.exclude(pk=request.user.pk):
                try:
                    Notification.objects.create(
                        recipient=p,
                        verb=f"Nouveau message sur la commande #{order.id}",
                        url=f"/commande/{order.id}/chat/"
                    )
                except Exception:
                    pass
            # Broadcast to group
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    f'order_{order.id}',
                    {
                        'type': 'chat.message',
                        'message': content,
                        'sender': request.user.username,
                        'created_at': msg.created_at.isoformat(),
                    }
                )
            except Exception:
                pass
            messages.success(request, "Réponse envoyée.")
            return redirect('admin_message_detail', conv_id=conv.id)

    # Mark messages as read for this staff user
    conv.messages.filter(read=False).exclude(sender=request.user).update(read=True)
    messages_qs = conv.messages.all()
    return render(request, 'shop/admin_message_detail.html', {'conversation': conv, 'messages': messages_qs})


# =========================
# ADMIN - INTERFACE SIMPLIFIÉE POUR STAFF
# =========================
from django.contrib.admin.views.decorators import staff_member_required
from .forms import OrderAdminForm, SubscriptionAdminForm

@staff_member_required
def admin_order_list(request):
    """Liste des commandes pour les admins (staff).
    Superuser voit tout, staff voit seulement les commandes assignées à lui.
    """
    qs = Order.objects.all().order_by('-created_at')
    if not request.user.is_superuser:
        qs = qs.filter(assigned_to=request.user)

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Pagination simple
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)

    return render(request, 'shop/admin_order_list.html', {'orders': orders_page})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_superuser and order.assigned_to and order.assigned_to != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette commande.")
        return redirect('admin_order_list')

    if request.method == 'POST':
        form = OrderAdminForm(request.POST, instance=order)
        if form.is_valid():
            old_status = order.status
            order = form.save(commit=False)
            order.save()
            # Historique
            if old_status != order.status:
                OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=order.status, changed_by=request.user)
                if order.user:
                    Notification.objects.create(recipient=order.user, verb=f"Le statut de votre commande #{order.id} est maintenant: {order.status}", url=f"/commande/{order.id}/")
            messages.success(request, "Commande mise à jour.")
            return redirect('admin_order_detail', order_id=order.id)
    else:
        form = OrderAdminForm(instance=order)

    status_history = order.status_history.all()
    return render(request, 'shop/admin_order_detail.html', {'order': order, 'form': form, 'status_history': status_history})


@staff_member_required
def admin_subscription_list(request):
    qs = Subscription.objects.all().order_by('-created_at')
    if not request.user.is_superuser:
        # optionally filter if you only want to show subscriptions you manage - keep all for admins
        qs = qs
    return render(request, 'shop/admin_subscription_list.html', {'subscriptions': qs})


@staff_member_required
def admin_subscription_detail(request, subscription_id):
    sub = get_object_or_404(Subscription, id=subscription_id)
    if request.method == 'POST':
        form = SubscriptionAdminForm(request.POST, instance=sub)
        if form.is_valid():
            form.save()
            messages.success(request, "Abonnement mis à jour.")
            return redirect('admin_subscription_detail', subscription_id=sub.id)
    else:
        form = SubscriptionAdminForm(instance=sub)
    return render(request, 'shop/admin_subscription_detail.html', {'subscription': sub, 'form': form})


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
def my_orders(request):
    """Page dédiée pour que le client consulte toutes ses commandes"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/orders_list.html', {'orders': orders})

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