"""Lógica de la transacción: cada operación se ejecuta de forma atómica, de modo
que la solicitud y su historial se guardan juntos o no se guarda nada."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count

from .models import COLORES_ESTADO, SeguimientoSolicitud, Solicitud


@transaction.atomic
def registrar_solicitud(form, usuario):
    """Crea la solicitud (estado Pendiente) y su primer seguimiento."""
    solicitud = form.save(commit=False)
    solicitud.creada_por = usuario
    solicitud.estado = Solicitud.Estado.PENDIENTE
    solicitud.save()
    SeguimientoSolicitud.objects.create(
        solicitud=solicitud, estado_anterior='', estado_nuevo=Solicitud.Estado.PENDIENTE,
        comentario='Solicitud registrada.', usuario=usuario,
    )
    return solicitud


@transaction.atomic
def gestionar_solicitud(pk, estado, autoridad, comentario, usuario):
    """Asigna autoridad y/o cambia el estado, dejando constancia en el historial."""
    # select_for_update bloquea la fila para evitar que dos usuarios la modifiquen a la vez
    solicitud = Solicitud.objects.select_for_update().get(pk=pk)
    if solicitud.esta_cerrada:
        raise ValidationError('La solicitud ya está cerrada y no admite modificaciones.')
    if estado not in solicitud.estados_permitidos():
        raise ValidationError('El cambio de estado solicitado no está permitido.')
    anterior = solicitud.estado
    solicitud.estado = estado
    solicitud.autoridad = autoridad
    solicitud.save()
    SeguimientoSolicitud.objects.create(
        solicitud=solicitud, estado_anterior=anterior, estado_nuevo=estado,
        autoridad=autoridad, comentario=comentario, usuario=usuario,
    )
    return solicitud


def resumen_por_estado(queryset=None):
    """Lista de dicts {codigo, etiqueta, total, color} para los dashboards."""
    queryset = Solicitud.objects.all() if queryset is None else queryset
    conteos = dict(queryset.order_by().values_list('estado').annotate(total=Count('id')))
    return [
        {'codigo': codigo, 'etiqueta': etiqueta, 'total': conteos.get(codigo, 0),
         'color': COLORES_ESTADO[codigo]}
        for codigo, etiqueta in Solicitud.Estado.choices
    ]
