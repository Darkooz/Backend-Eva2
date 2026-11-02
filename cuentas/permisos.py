"""Matriz de permisos por perfil.

Cada perfil es un Grupo de Django con permisos del sistema de permisos nativo
(view / add / change / delete + el permiso personalizado `gestionar_solicitud`).
"""
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError

from .perfiles import ADMINISTRADOR, ADMINISTRATIVO, SUPERVISOR

CRUD = ['view', 'add', 'change', 'delete']

# (app, modelo, acciones)
PERMISOS_POR_PERFIL = {
    # Acceso total al sistema, incluida la gestión de usuarios
    ADMINISTRADOR: [
        ('institucion', 'delegacion', CRUD),
        ('institucion', 'autoridad', CRUD),
        ('solicitudes', 'solicitud', CRUD + ['gestionar']),
        ('solicitudes', 'seguimientosolicitud', ['view']),
        ('auth', 'user', CRUD),
        ('auth', 'group', ['view']),
    ],
    # Permisos intermedios: opera mantenedores y gestiona solicitudes, sin eliminar ni administrar usuarios
    SUPERVISOR: [
        ('institucion', 'delegacion', ['view', 'add', 'change']),
        ('institucion', 'autoridad', ['view', 'add', 'change']),
        ('solicitudes', 'solicitud', ['view', 'add', 'gestionar']),
        ('solicitudes', 'seguimientosolicitud', ['view']),
    ],
    # Permisos mínimos: consulta mantenedores y registra solicitudes
    ADMINISTRATIVO: [
        ('institucion', 'delegacion', ['view']),
        ('institucion', 'autoridad', ['view']),
        ('solicitudes', 'solicitud', ['view', 'add']),
    ],
}


def sincronizar_grupos():
    """Crea los grupos y les asigna exactamente los permisos de la matriz."""
    try:
        for perfil, definicion in PERMISOS_POR_PERFIL.items():
            grupo, _ = Group.objects.get_or_create(name=perfil)
            permisos = []
            for app_label, nombre_modelo, acciones in definicion:
                modelo = apps.get_model(app_label, nombre_modelo)
                tipo = ContentType.objects.get_for_model(modelo)
                for accion in acciones:
                    permiso, _ = Permission.objects.get_or_create(
                        content_type=tipo,
                        codename=f'{accion}_{nombre_modelo}',
                        defaults={'name': f'Puede {accion} {modelo._meta.verbose_name}'},
                    )
                    permisos.append(permiso)
            grupo.permissions.set(permisos)
    except (LookupError, DatabaseError):
        # Migraciones parciales (p. ej. `migrate institucion 0001`): se omite.
        pass
