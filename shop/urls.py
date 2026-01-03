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
    
    # Authentification
    path('inscription/', views.signup, name='signup'),
    path('connexion/', views.user_login, name='login'),
    path('deconnexion/', views.user_logout, name='logout'),
    
    # Profil
    path('profil/', views.profile, name='profile'),
    path('profil/modifier/', views.edit_profile, name='edit_profile'),
]