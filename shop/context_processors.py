from .cart import Cart

def cart_context(request):
    """Rend le panier disponible dans tous les templates"""
    unread = 0
    admin_unread_messages = 0
    if request.user.is_authenticated:
        try:
            unread = request.user.notifications.filter(unread=True).count()
        except Exception:
            # If notifications relation is not available yet (tests/migrations), fall back to 0
            unread = 0
        # Compute admin unread messages only for staff
        if getattr(request.user, 'is_staff', False):
            try:
                # Count messages not sent by the user and that are unread across conversations where the user participates
                admin_unread_messages = sum(
                    c.messages.filter(read=False).exclude(sender=request.user).count()
                    for c in request.user.conversations.all()
                )
            except Exception:
                admin_unread_messages = 0
    return {
        'cart': Cart(request),
        'unread_notifications_count': unread,
        'admin_unread_messages_count': admin_unread_messages,
    }