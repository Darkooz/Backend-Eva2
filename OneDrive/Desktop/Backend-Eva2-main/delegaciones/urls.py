from django.urls import path
from . import views

app_name = 'delegaciones'

urlpatterns = [
    path('', views.DelegacionListView.as_view(), name='delegacion_list'),
    path('nueva/', views.DelegacionCreateView.as_view(), name='delegacion_create'),
    path('<int:pk>/editar/', views.DelegacionUpdateView.as_view(), name='delegacion_update'),
    path('<int:pk>/eliminar/', views.DelegacionDeleteView.as_view(), name='delegacion_delete'),
    path('contacto/', views.contacto_delegaciones, name='contacto'),
]
