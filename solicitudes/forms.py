from django import forms

from config.bootstrap import BootstrapFormMixin
from institucion.forms import validar_telefono
from institucion.models import Autoridad, Delegacion
from .models import Solicitud


class SolicitudForm(BootstrapFormMixin, forms.ModelForm):
    """Formulario de registro de una solicitud ciudadana."""

    class Meta:
        model = Solicitud
        fields = ['solicitante_nombre', 'solicitante_email', 'solicitante_telefono',
                  'tipo', 'prioridad', 'delegacion', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 4}),
                   'solicitante_telefono': forms.TextInput(attrs={'placeholder': 'Ej: 9 1234 5678'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delegacion'].queryset = Delegacion.objects.order_by('nombre')
        self.fields['delegacion'].empty_label = '— Seleccione una delegación —'

    def clean_solicitante_nombre(self):
        nombre = ' '.join(self.cleaned_data['solicitante_nombre'].split())
        if len(nombre.split(' ')) < 2:
            raise forms.ValidationError('Ingrese al menos nombre y apellido del solicitante.')
        return nombre

    def clean_solicitante_telefono(self):
        return validar_telefono(self.cleaned_data.get('solicitante_telefono'))

    def clean_descripcion(self):
        descripcion = self.cleaned_data['descripcion'].strip()
        if len(descripcion) < 15:
            raise forms.ValidationError('Describa el problema con al menos 15 caracteres.')
        return descripcion

    def clean(self):
        datos = super().clean()
        if not datos.get('solicitante_email') and not datos.get('solicitante_telefono'):
            raise forms.ValidationError('Indique al menos un medio de contacto: correo o teléfono.')
        return datos


class GestionSolicitudForm(BootstrapFormMixin, forms.Form):
    """Asignación de autoridad y cambio de estado (parte 2 de la transacción)."""
    estado = forms.ChoiceField(label='Estado')
    autoridad = forms.ModelChoiceField(
        label='Autoridad asignada', queryset=Autoridad.objects.order_by('nombre'),
        required=False, empty_label='— Sin asignar —',
    )
    comentario = forms.CharField(
        label='Comentario', required=False, widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Obligatorio al resolver o rechazar la solicitud.',
    )

    def __init__(self, *args, solicitud, **kwargs):
        super().__init__(*args, **kwargs)
        self.solicitud = solicitud
        etiquetas = dict(Solicitud.Estado.choices)
        self.fields['estado'].choices = [(e, etiquetas[e]) for e in solicitud.estados_permitidos()]
        self.initial.setdefault('estado', solicitud.estado)
        self.initial.setdefault('autoridad', solicitud.autoridad_id)

    def clean(self):
        datos = super().clean()
        estado, autoridad = datos.get('estado'), datos.get('autoridad')
        comentario = (datos.get('comentario') or '').strip()
        if estado is None:
            return datos
        if estado == self.solicitud.estado and autoridad == self.solicitud.autoridad:
            raise forms.ValidationError('No hay cambios que guardar: modifique el estado o la autoridad asignada.')
        if estado in (Solicitud.Estado.EN_PROCESO, Solicitud.Estado.RESUELTA) and autoridad is None:
            self.add_error('autoridad', 'Debe asignar una autoridad para poner la solicitud en proceso o resolverla.')
        if estado in (Solicitud.Estado.RESUELTA, Solicitud.Estado.RECHAZADA) and not comentario:
            self.add_error('comentario', 'Debe indicar un comentario al resolver o rechazar la solicitud.')
        datos['comentario'] = comentario
        return datos
