from django import forms


class BootstrapFormMixin:
    """Aplica las clases de Bootstrap 5 a los widgets y marca con `is-invalid`
    los campos que fallan la validación. Se usa en todos los formularios."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            self._agregar_clase(field.widget, self._clase_para(field.widget))

    @staticmethod
    def _clase_para(widget):
        if isinstance(widget, forms.CheckboxInput):
            return 'form-check-input'
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            return 'form-select'
        return 'form-control'

    @staticmethod
    def _agregar_clase(widget, clase):
        actuales = widget.attrs.get('class', '')
        widget.attrs['class'] = f'{actuales} {clase}'.strip()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for nombre in self.errors:
                if nombre in self.fields:
                    self._agregar_clase(self.fields[nombre].widget, 'is-invalid')
