from django.urls import path
from . import views

app_name = 'institucion'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('historia/', views.historia, name='historia'),
]