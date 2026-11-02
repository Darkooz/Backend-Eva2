from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm, UserCreationForm)
from django.contrib.auth.models import Group

from config.bootstrap import BootstrapFormMixin
from .perfiles import PERFILES

User = get_user_model()


def _grupos_de_perfil():
    return Group.objects.filter(name__in=PERFILES).order_by('name')


def _validar_email_unico(email, excluir_pk=None):
    email = email.strip().lower()
    repetidos = User.objects.filter(email__iexact=email)
    if excluir_pk:
        repetidos = repetidos.exclude(pk=excluir_pk)
    if repetidos.exists():
        raise forms.ValidationError('Ya existe un usuario con ese correo electrónico.')
    return email


# --------------------------- Inicio de sesión ---------------------------
class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['password'].label = 'Contraseña'
        self.fields['username'].widget.attrs.update({'placeholder': 'Nombre de usuario', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'placeholder': 'Contraseña'})


# --------------------------- Recuperación de contraseña ---------------------------
class RecuperarClaveForm(BootstrapFormMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Correo electrónico'
        self.fields['email'].widget.attrs.update({'placeholder': 'usuario@correo.cl', 'autofocus': True})

    def save(self, *args, **kwargs):
        # El protocolo del enlace del correo se controla desde el .env (PASSWORD_RESET_USE_HTTPS)
        kwargs['use_https'] = kwargs.get('use_https', False) or settings.PASSWORD_RESET_USE_HTTPS
        return super().save(*args, **kwargs)


class NuevaClaveForm(BootstrapFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirmar nueva contraseña'


# --------------------------- Gestión de usuarios ---------------------------
class UsuarioCrearForm(BootstrapFormMixin, UserCreationForm):
    grupo = forms.ModelChoiceField(
        label='Perfil', queryset=Group.objects.none(), empty_label='— Seleccione un perfil —',
        help_text='Define los permisos del usuario dentro del sistema.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].queryset = _grupos_de_perfil()
        self.fields['username'].label = 'Nombre de usuario'
        for nombre in ('first_name', 'last_name', 'email'):
            self.fields[nombre].required = True
        self.fields['first_name'].label = 'Nombres'
        self.fields['last_name'].label = 'Apellidos'
        self.fields['email'].label = 'Correo electrónico'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.order_fields(['username', 'first_name', 'last_name', 'email', 'grupo', 'password1', 'password2'])

    def clean_email(self):
        return _validar_email_unico(self.cleaned_data['email'])

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            usuario.groups.set([self.cleaned_data['grupo']])
        return usuario


class UsuarioEditarForm(BootstrapFormMixin, forms.ModelForm):
    grupo = forms.ModelChoiceField(label='Perfil', queryset=Group.objects.none(), empty_label=None)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_active')
        labels = {'first_name': 'Nombres', 'last_name': 'Apellidos',
                  'email': 'Correo electrónico', 'is_active': 'Usuario activo'}

    def __init__(self, *args, usuario_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].queryset = _grupos_de_perfil()
        for nombre in ('first_name', 'last_name', 'email'):
            self.fields[nombre].required = True
        grupo_actual = self.instance.groups.filter(name__in=PERFILES).first()
        self.fields['grupo'].initial = grupo_actual
        # Un usuario no puede cambiar su propio perfil ni desactivarse (evita bloquearse)
        if usuario_actual is not None and usuario_actual.pk == self.instance.pk:
            for nombre in ('grupo', 'is_active'):
                self.fields[nombre].disabled = True
                self.fields[nombre].required = False
            self.fields['grupo'].help_text = 'No puede modificar su propio perfil ni desactivar su cuenta.'
        elif self.instance.is_superuser:
            self.fields['grupo'].required = False
        self.order_fields(['first_name', 'last_name', 'email', 'grupo', 'is_active'])

    def clean_email(self):
        return _validar_email_unico(self.cleaned_data['email'], self.instance.pk)

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        grupo = self.cleaned_data.get('grupo')
        if commit and not self.fields['grupo'].disabled and grupo is not None:
            usuario.groups.set([grupo])
        return usuario
