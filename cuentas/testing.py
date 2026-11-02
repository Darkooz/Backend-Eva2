"""Utilidades compartidas por las pruebas automáticas."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

CLAVE = 'Muni-Prueba-2026!'


def crear_usuario(perfil, username=None, **extra):
    User = get_user_model()
    username = username or perfil.lower()
    usuario = User.objects.create_user(
        username=username, password=CLAVE, email=f'{username}@muni.local',
        first_name=perfil, last_name='Prueba', **extra,
    )
    usuario.groups.add(Group.objects.get(name=perfil))
    return usuario
