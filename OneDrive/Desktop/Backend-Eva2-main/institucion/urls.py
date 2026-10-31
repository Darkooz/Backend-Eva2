from django.urls import path
from . import views

app_name = 'institucion'

urlpatterns = [
    # Públicas
    path('', views.inicio, name='inicio'),
    path('historia/', views.historia, name='historia'),

    # Mantenedor de autoridades (protegido)
    path('autoridades/', views.AutoridadListView.as_view(), name='autoridad_list'),
    path('autoridades/nueva/', views.AutoridadCreateView.as_view(), name='autoridad_create'),
    path('autoridades/<int:pk>/editar/', views.AutoridadUpdateView.as_view(), name='autoridad_update'),
    path('autoridades/<int:pk>/eliminar/', views.AutoridadDeleteView.as_view(), name='autoridad_delete'),
]
