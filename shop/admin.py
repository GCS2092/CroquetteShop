from django.contrib import admin
from .models import Product, DeliveryLocation, Order, OrderItem, Subscription, RewardPoint
from .models import UserProfile
from .models import Notification, OrderStatusHistory, Conversation, Message

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_active']


@admin.register(DeliveryLocation)
class DeliveryLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'address']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_customer', 'delivery_location', 'total_amount', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'delivery_location', 'created_at', 'assigned_to']
    search_fields = ['guest_name', 'guest_email', 'user__username', 'assigned_to__username']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    actions = ['claim_orders', 'mark_confirmed', 'mark_delivered', 'mark_cancelled']

    def get_customer(self, obj):
        if obj.user:
            return obj.user.username
        return f"{obj.guest_name} (invité)"
    get_customer.short_description = 'Client'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all orders
        if request.user.is_superuser:
            return qs
        # Staff (admin) see only orders assigned to them
        if request.user.is_staff:
            return qs.filter(assigned_to=request.user)
        # Other users should not access admin at all normally
        return qs.none()

    def claim_orders(self, request, queryset):
        """Action admin: s'assigner les commandes sélectionnées"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{updated} commande(s) assignée(s) à vous.")
    claim_orders.short_description = "S'assigner les commandes sélectionnées"

    def _bulk_change_status(self, request, queryset, new_status):
        for order in queryset:
            old_status = order.status
            order.status = new_status
            order.save()
            # Créer l'historique avec l'utilisateur qui effectue l'action
            OrderStatusHistory.objects.create(order=order, old_status=old_status, new_status=new_status, changed_by=request.user)
            # Notifier le client
            if order.user:
                Notification.objects.create(recipient=order.user, verb=f"Le statut de votre commande #{order.id} est maintenant: {new_status}", url=f"/commande/{order.id}/")
        self.message_user(request, f"Statut changé vers '{new_status}' pour {queryset.count()} commande(s).")

    def mark_confirmed(self, request, queryset):
        self._bulk_change_status(request, queryset, 'confirmed')
    mark_confirmed.short_description = "Marquer comme confirmée"

    def mark_delivered(self, request, queryset):
        self._bulk_change_status(request, queryset, 'delivered')
    mark_delivered.short_description = "Marquer comme livrée"

    def mark_cancelled(self, request, queryset):
        self._bulk_change_status(request, queryset, 'cancelled')
    mark_cancelled.short_description = "Marquer comme annulée"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'frequency', 'status', 'next_delivery', 'created_at']
    list_filter = ['status', 'frequency']
    search_fields = ['user__username']
    filter_horizontal = ['products']


@admin.register(RewardPoint)
class RewardPointAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'total_earned', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['total_earned', 'updated_at']


# Enregistrer les nouveaux modèles pour gérer historique, notifications et chat
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'verb', 'unread', 'created_at']
    search_fields = ['recipient__username', 'verb']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'old_status', 'new_status', 'changed_by', 'created_at']
    search_fields = ['order__id', 'changed_by__username']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'created_at']
    search_fields = ['order__id']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'created_at']
    search_fields = ['sender__username', 'conversation__order__id']
