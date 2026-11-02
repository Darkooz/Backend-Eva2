from django.conf import settings
from django.db import models

COLORES_ESTADO = {
    'pendiente': 'warning',
    'en_proceso': 'primary',
    'resuelta': 'success',
    'rechazada': 'secondary',
}
COLORES_PRIORIDAD = {'baja': 'secondary', 'media': 'info', 'alta': 'danger'}


class Solicitud(models.Model):
    """Solicitud ciudadana ingresada en una delegación y asignada a una autoridad.

    Es la entidad central de la transacción operacional: relaciona
    Delegación (PROTECT), Autoridad (SET_NULL) y Usuario (quien la registra).
    """

    class Tipo(models.TextChoices):
        ALUMBRADO = 'alumbrado', 'Alumbrado público'
        ASEO = 'aseo', 'Aseo y ornato'
        VIALIDAD = 'vialidad', 'Calles y veredas'
        SEGURIDAD = 'seguridad', 'Seguridad comunal'
        AREAS_VERDES = 'areas_verdes', 'Áreas verdes'
        OTRO = 'otro', 'Otro'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROCESO = 'en_proceso', 'En proceso'
        RESUELTA = 'resuelta', 'Resuelta'
        RECHAZADA = 'rechazada', 'Rechazada'

    class Prioridad(models.TextChoices):
        BAJA = 'baja', 'Baja'
        MEDIA = 'media', 'Media'
        ALTA = 'alta', 'Alta'

    # Flujo permitido de estados
    TRANSICIONES = {
        Estado.PENDIENTE: [Estado.EN_PROCESO, Estado.RECHAZADA],
        Estado.EN_PROCESO: [Estado.RESUELTA, Estado.RECHAZADA],
        Estado.RESUELTA: [],
        Estado.RECHAZADA: [],
    }

    solicitante_nombre = models.CharField('Nombre del solicitante', max_length=100)
    solicitante_email = models.EmailField('Correo del solicitante', blank=True)
    solicitante_telefono = models.CharField('Teléfono del solicitante', max_length=20, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    descripcion = models.TextField('Descripción')
    delegacion = models.ForeignKey(
        'institucion.Delegacion', on_delete=models.PROTECT, related_name='solicitudes',
        verbose_name='Delegación',
    )
    autoridad = models.ForeignKey(
        'institucion.Autoridad', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitudes_asignadas', verbose_name='Autoridad asignada',
    )
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitudes_creadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion', '-id']
        verbose_name = 'solicitud'
        verbose_name_plural = 'solicitudes'
        permissions = [
            ('gestionar_solicitud', 'Puede asignar autoridad y cambiar el estado de solicitudes'),
        ]

    def __str__(self):
        return f'Solicitud #{self.pk} - {self.get_tipo_display()}'

    @property
    def esta_cerrada(self):
        return self.estado in (self.Estado.RESUELTA, self.Estado.RECHAZADA)

    @property
    def color_estado(self):
        return COLORES_ESTADO.get(self.estado, 'secondary')

    @property
    def color_prioridad(self):
        return COLORES_PRIORIDAD.get(self.prioridad, 'secondary')

    def estados_permitidos(self):
        """Estado actual + los estados a los que puede avanzar."""
        return [self.estado] + [e.value for e in self.TRANSICIONES[self.estado]]


class SeguimientoSolicitud(models.Model):
    """Historial inmutable de cada cambio realizado a una solicitud."""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='seguimientos')
    estado_anterior = models.CharField(max_length=15, blank=True)
    estado_nuevo = models.CharField(max_length=15, choices=Solicitud.Estado.choices)
    autoridad = models.ForeignKey(
        'institucion.Autoridad', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguimientos',
    )
    comentario = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seguimientos_realizados',
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'id']
        verbose_name = 'seguimiento de solicitud'
        verbose_name_plural = 'seguimientos de solicitudes'

    def __str__(self):
        return f'{self.solicitud} → {self.estado_nuevo}'

    @property
    def color_estado(self):
        return COLORES_ESTADO.get(self.estado_nuevo, 'secondary')
