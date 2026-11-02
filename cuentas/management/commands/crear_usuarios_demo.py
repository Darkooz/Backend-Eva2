import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from cuentas.perfiles import ADMINISTRADOR, ADMINISTRATIVO, SUPERVISOR
from cuentas.permisos import sincronizar_grupos

DEMO = [
    ('admin_demo', 'Ana', 'Administradora', ADMINISTRADOR),
    ('supervisor_demo', 'Sergio', 'Supervisor', SUPERVISOR),
    ('administrativo_demo', 'Andrea', 'Administrativa', ADMINISTRATIVO),
]


class Command(BaseCommand):
    help = 'Crea un usuario de ejemplo por cada perfil (para la revisión del sistema)'

    def add_arguments(self, parser):
        parser.add_argument('--password', help='Contraseña común (si se omite se genera una aleatoria)')

    def handle(self, *args, **options):
        sincronizar_grupos()
        User = get_user_model()
        password = options['password'] or secrets.token_urlsafe(9)
        for username, nombre, apellido, perfil in DEMO:
            usuario, creado = User.objects.get_or_create(
                username=username,
                defaults={'first_name': nombre, 'last_name': apellido, 'email': f'{username}@muni.local'},
            )
            usuario.set_password(password)
            usuario.save()
            usuario.groups.set([Group.objects.get(name=perfil)])
            self.stdout.write(f'{"Creado" if creado else "Actualizado"}: {username} ({perfil})')
        self.stdout.write(self.style.SUCCESS(f'Contraseña de los usuarios demo: {password}'))
        self.stdout.write('Edite el correo de cada uno desde Usuarios para probar la recuperación de contraseña.')
