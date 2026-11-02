from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect


class BuscadorMixin:
    """Búsqueda (?q=) sobre los campos indicados + `querystring` para paginar
    conservando los filtros activos."""
    campos_busqueda = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q and self.campos_busqueda:
            filtro = Q()
            for campo in self.campos_busqueda:
                filtro |= Q(**{f'{campo}__icontains': q})
            queryset = queryset.filter(filtro)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop('page', None)
        contexto['q'] = self.request.GET.get('q', '').strip()
        contexto['querystring'] = parametros.urlencode()
        return contexto


class EliminarSeguroMixin:
    """Para DeleteView: muestra un mensaje en vez de un error 500 cuando el
    registro está protegido por una relación (on_delete=PROTECT)."""
    mensaje_exito = 'Registro eliminado correctamente.'
    mensaje_protegido = 'No se puede eliminar: el registro tiene información asociada.'

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.mensaje_protegido)
            return redirect(self.get_success_url())
        messages.success(self.request, self.mensaje_exito)
        return respuesta
