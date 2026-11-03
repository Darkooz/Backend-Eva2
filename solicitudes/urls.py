from django.urls import path
from . import views

app_name = 'solicitudes'

urlpatterns = [
    path('', views.SolicitudListView.as_view(), name='solicitud_list'),
    path('nueva/', views.SolicitudCreateView.as_view(), name='solicitud_create'),
    path('<int:pk>/', views.SolicitudDetailView.as_view(), name='solicitud_detail'),
    path('adjuntos/<int:pk>/', views.adjunto_descargar, name='adjunto_descargar'),
    path('<int:pk>/eliminar/', views.SolicitudDeleteView.as_view(), name='solicitud_delete'),
]
