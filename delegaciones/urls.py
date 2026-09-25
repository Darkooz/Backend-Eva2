from django.urls import path
from . import views  

urlpatterns = [
    
    path('', views.lista_delegaciones, name='lista_delegaciones'),
    path('contacto/', views.contacto_delegaciones, name='contacto_delegaciones'),
]