from django.core.management.base import BaseCommand

from cuentas.permisos import PERMISOS_POR_PERFIL, sincronizar_grupos


class Command(BaseCommand):
    help = 'Crea/actualiza los grupos Administrador, Supervisor y Administrativo con sus permisos'

    def handle(self, *args, **options):
        sincronizar_grupos()
        for perfil in PERMISOS_POR_PERFIL:
            self.stdout.write(self.style.SUCCESS(f'Grupo «{perfil}» sincronizado'))
