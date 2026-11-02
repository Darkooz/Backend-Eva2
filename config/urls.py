from django.urls import path, include

# Django Admin ya no se publica: desde la Eva 3 toda la gestión se realiza
# mediante interfaces propias (Django Templates + Bootstrap).
urlpatterns = [
    path('cuentas/', include('cuentas.urls')),
    path('delegaciones/', include('delegaciones.urls')),
    path('solicitudes/', include('solicitudes.urls')),
    path('', include('institucion.urls')),
]
