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