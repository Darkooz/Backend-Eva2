from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sincronizar(sender, **kwargs):
    from .permisos import sincronizar_grupos
    sincronizar_grupos()


class CuentasConfig(AppConfig):
    name = 'cuentas'

    def ready(self):
        # Cada vez que se ejecuta `migrate` los grupos y sus permisos quedan al día.
        post_migrate.connect(_sincronizar, sender=self)
