import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from institucion.models import Delegacion, Autoridad

class Command(BaseCommand):
    help = 'Carga delegaciones y autoridades desde los JSON a la base de datos'

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)

        with open(base / 'delegaciones' / 'delegaciones.json', encoding='utf-8') as f:
            for d in json.load(f):
                Delegacion.objects.update_or_create(
                    nombre=d['nombre'],
                    defaults={
                        'encargado': d.get('encargado'),
                        'direccion': d['direccion'],
                        'telefono': d.get('telefono'),
                    },
                )

        with open(base / 'institucion' / 'autoridades.json', encoding='utf-8') as f:
            for a in json.load(f):
                Autoridad.objects.update_or_create(
                    nombre=a['nombre'],
                    cargo=a['cargo'],
                    defaults={'descripcion': a.get('descripcion')},
                )

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Delegacion.objects.count()} delegaciones y {Autoridad.objects.count()} autoridades'
        ))