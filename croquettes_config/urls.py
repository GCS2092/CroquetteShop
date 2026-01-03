# croquettes_config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop import views  # Ajoute ça

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Tes URLs personnalisées pour l'auth
    path('connexion/', views.user_login, name='login'),
    path('inscription/', views.signup, name='signup'),
    path('deconnexion/', views.user_logout, name='logout'),
    
    # Profil et autres
    path('profil/', views.profile, name='profile'),
    path('profil/modifier/', views.edit_profile, name='edit_profile'),
    path('commande/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Page récompenses
    path('recompenses/', views.rewards, name='rewards'),
    
    # Tes URLs shop
    path('', include('shop.urls')),
]

# Pour les médias en dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)