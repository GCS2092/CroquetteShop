from django.contrib import admin
from .models import Product, DeliveryLocation, Order, OrderItem, Subscription, RewardPoint
from .models import UserProfile

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
    list_display = ['id', 'get_customer', 'delivery_location', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'delivery_location', 'created_at']
    search_fields = ['guest_name', 'guest_email', 'user__username']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def get_customer(self, obj):
        if obj.user:
            return obj.user.username
        return f"{obj.guest_name} (invité)"
    get_customer.short_description = 'Client'


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