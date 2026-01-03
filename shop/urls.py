from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('recompenses/', views.rewards, name='rewards'),  # ✅ AJOUTÉ
    
    # Panier
    path('panier/', views.cart_detail, name='cart_detail'),
    path('panier/ajouter/<int:product_id>/', views.cart_add, name='cart_add'),
    path('panier/retirer/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
    # Commandes
    path('commander/', views.checkout, name='checkout'),
    path('commande/confirmation/<int:order_id>/', views.order_success, name='order_success'),
    path('commande/<int:order_id>/', views.order_detail, name='order_detail'),
    path('commande/<int:order_id>/chat/', views.order_chat, name='order_chat'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Authentification
    path('inscription/', views.signup, name='signup'),
    path('connexion/', views.user_login, name='login'),
    path('deconnexion/', views.user_logout, name='logout'),
    
    # Profil
    path('profil/', views.profile, name='profile'),
    path('profil/modifier/', views.edit_profile, name='edit_profile'),
    path('mes-commandes/', views.my_orders, name='my_orders'),

    # Staff pages (avoid conflicting with Django admin at /admin/)
    path('staff/commandes/', views.admin_order_list, name='admin_order_list'),
    path('staff/commande/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('staff/abonnements/', views.admin_subscription_list, name='admin_subscription_list'),
    path('staff/abonnement/<int:subscription_id>/', views.admin_subscription_detail, name='admin_subscription_detail'),

    # Notification AJAX endpoints
    path('notifications/mark_read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark_all_read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Staff messages
    path('staff/messages/', views.admin_messages_list, name='admin_messages_list'),
    path('staff/message/<int:conv_id>/', views.admin_message_detail, name='admin_message_detail'),
]