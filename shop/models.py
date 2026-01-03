from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    """Modèle pour les produits (croquettes)"""
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (XOF)")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image")
    stock = models.IntegerField(default=0, verbose_name="Stock disponible")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class DeliveryLocation(models.Model):
    """Lieux de livraison (ajoutés par l'admin)"""
    name = models.CharField(max_length=200, verbose_name="Nom du lieu")
    address = models.TextField(blank=True, verbose_name="Adresse complète")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Lieu de livraison"
        verbose_name_plural = "Lieux de livraison"
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Commandes (clients connectés ou invités)"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    
    # Si l'utilisateur est connecté, on lie la commande à son compte
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Utilisateur")

    # Optionnel : commande assignée à un admin (vendeur = is_staff)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True},
        related_name='assigned_orders',
        verbose_name='Assigné à (admin)'
    )
    
    # Informations pour les invités (obligatoires si user est null)
    guest_name = models.CharField(max_length=200, blank=True, verbose_name="Nom (invité)")
    guest_email = models.EmailField(blank=True, verbose_name="Email (invité)")
    guest_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone (invité)")
    
    delivery_location = models.ForeignKey(DeliveryLocation, on_delete=models.PROTECT, verbose_name="Lieu de livraison")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total (XOF)")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"Commande #{self.id} - {self.user.username}"
        return f"Commande #{self.id} - {self.guest_name} (invité)"


class OrderItem(models.Model):
    """Articles dans une commande"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Produit")
    quantity = models.IntegerField(default=1, verbose_name="Quantité")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (XOF)")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def get_total(self):
        return self.quantity * self.price


class Subscription(models.Model):
    """Abonnements (activés par l'admin uniquement)"""
    FREQUENCY_CHOICES = [
        ('weekly', 'Hebdomadaire'),
        ('biweekly', 'Toutes les 2 semaines'),
        ('monthly', 'Mensuel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('cancelled', 'Annulé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    products = models.ManyToManyField(Product, verbose_name="Produits (lot)")
    delivery_location = models.ForeignKey(DeliveryLocation, on_delete=models.PROTECT, verbose_name="Lieu de livraison")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Fréquence")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Statut")
    next_delivery = models.DateField(verbose_name="Prochaine livraison")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
    
    def __str__(self):
        return f"Abonnement de {self.user.username} - {self.get_frequency_display()}"


class RewardPoint(models.Model):
    """Points de fidélité"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    points = models.IntegerField(default=0, verbose_name="Points")
    total_earned = models.IntegerField(default=0, verbose_name="Total gagné")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Points de fidélité"
        verbose_name_plural = "Points de fidélité"
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points"

class UserProfile(models.Model):
    """Profil utilisateur étendu"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.username}"


# Signal pour créer automatiquement un profil et des points lors de l'inscription
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement un profil et des points pour chaque nouvel utilisateur"""
    if created:
        UserProfile.objects.create(user=instance)
        RewardPoint.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil quand l'utilisateur est sauvegardé"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# --- Notifications / Chat / Historique des statuts ---
class Notification(models.Model):
    """Notifications pour utilisateurs (site only)."""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    verb = models.CharField(max_length=255, verbose_name='Action')
    url = models.CharField(max_length=255, blank=True, verbose_name='Lien relatif')
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.recipient.username} - {self.verb}"


class OrderStatusHistory(models.Model):
    """Historique des changements de statut d'une commande."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, verbose_name='Ancien statut')
    new_status = models.CharField(max_length=20, verbose_name='Nouveau statut')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Modifié par')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order.id}: {self.old_status} -> {self.new_status}"


class Conversation(models.Model):
    """Conversation liée à une commande (client <-> admin)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='conversations')
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation #{self.id} (Order #{self.order.id})"


class Message(models.Model):
    """Message d'une conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.id} by {self.sender.username}"


# Signals pour notifications et historique de statut
from django.db.models.signals import post_save, pre_save

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    # Nouvelle commande : notifier les admin (is_staff=True) et l'utilisateur
    if created:
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                verb=f"Nouvelle commande #{instance.id}",
                url=f"/admin/shop/order/{instance.id}/change/"
            )
        if instance.user:
            Notification.objects.create(
                recipient=instance.user,
                verb=f"Votre commande #{instance.id} a été passée.",
                url=f"/commande/{instance.id}/"
            )


# Lorsqu'une Notification est créée, on envoie aussi un push via Channels au destinataire
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    if not created:
        return
    channel_layer = get_channel_layer()
    group = f"notifications_{instance.recipient.id}"
    payload = {
        'id': instance.id,
        'verb': instance.verb,
        'url': instance.url,
        'created_at': instance.created_at.isoformat(),
    }
    try:
        async_to_sync(channel_layer.group_send)(group, {
            'type': 'notify',
            'payload': payload,
        })
    except Exception:
        # Ne pas planter si Channel layer n'est pas disponible (dev without Redis)
        pass

@receiver(pre_save, sender=Order)
def order_status_change(sender, instance, **kwargs):
    # Si la commande existe déjà, on détecte changement de statut
    if not instance.pk:
        return
    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return
    if old.status != instance.status:
        OrderStatusHistory.objects.create(
            order=instance,
            old_status=old.status,
            new_status=instance.status,
            changed_by=None
        )
        # Notifications côté client et admin assigné
        if instance.user:
            Notification.objects.create(
                recipient=instance.user,
                verb=f"Le statut de votre commande #{instance.id} est passé de {old.status} à {instance.status}.",
                url=f"/commande/{instance.id}/"
            )
        if instance.assigned_to:
            Notification.objects.create(
                recipient=instance.assigned_to,
                verb=f"Le statut de la commande #{instance.id} a changé: {instance.status}.",
                url=f"/admin/shop/order/{instance.id}/change/"
            )
