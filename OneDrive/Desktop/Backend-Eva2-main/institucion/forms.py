import re

from django import forms

from config.bootstrap import BootstrapFormMixin
from .models import Autoridad, Delegacion

PATRON_TELEFONO = re.compile(r'^[0-9+()\-\s]{6,20}$')


def validar_telefono(valor):
    if valor and not PATRON_TELEFONO.match(valor):
        raise forms.ValidationError(
            'Ingrese un teléfono válido (solo números, espacios, +, - y paréntesis; entre 6 y 20 caracteres).'
        )
    return valor


class DelegacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ['nombre', 'encargado', 'direccion', 'telefono']
        labels = {'nombre': 'Nombre de la delegación', 'encargado': 'Encargado/a',
                  'direccion': 'Dirección', 'telefono': 'Teléfono'}
        widgets = {'telefono': forms.TextInput(attrs={'placeholder': 'Ej: 512 206518'})}

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        repetidas = Delegacion.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise forms.ValidationError('Ya existe una delegación con ese nombre.')
        return nombre

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))


class AutoridadForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Autoridad
        fields = ['nombre', 'cargo', 'delegacion', 'descripcion']
        labels = {'nombre': 'Nombre completo', 'cargo': 'Cargo',
                  'delegacion': 'Delegación (opcional)', 'descripcion': 'Descripción'}
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if len(nombre.split(' ')) < 2:
            raise forms.ValidationError('Ingrese al menos nombre y apellido.')
        return nombre

    def clean(self):
        datos = super().clean()
        nombre, cargo = datos.get('nombre'), datos.get('cargo')
        if nombre and cargo:
            repetidas = Autoridad.objects.filter(nombre__iexact=nombre, cargo__iexact=cargo)
            if repetidas.exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Ya existe una autoridad con ese nombre y cargo.')
        return datos
