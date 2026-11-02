from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from config.mixins import BuscadorMixin, EliminarSeguroMixin
from institucion.forms import DelegacionForm
from institucion.models import Delegacion


class DelegacionBase(LoginRequiredMixin, PermissionRequiredMixin):
    model = Delegacion
    success_url = reverse_lazy('delegaciones:delegacion_list')


class DelegacionListView(DelegacionBase, BuscadorMixin, ListView):
    permission_required = 'institucion.view_delegacion'
    template_name = 'delegaciones/delegacion_list.html'
    context_object_name = 'delegaciones'
    paginate_by = 8
    campos_busqueda = ('nombre', 'encargado', 'direccion', 'telefono')

    def get_queryset(self):
        return super().get_queryset().annotate(
            total_autoridades=Count('autoridades', distinct=True),
            total_solicitudes=Count('solicitudes', distinct=True),
        ).order_by('nombre')


class DelegacionCreateView(DelegacionBase, SuccessMessageMixin, CreateView):
    permission_required = 'institucion.add_delegacion'
    form_class = DelegacionForm
    template_name = 'crud/formulario.html'
    success_message = 'Delegación «%(nombre)s» creada correctamente.'
    extra_context = {'titulo': 'Nueva delegación', 'volver_url': reverse_lazy('delegaciones:delegacion_list')}


class DelegacionUpdateView(DelegacionBase, SuccessMessageMixin, UpdateView):
    permission_required = 'institucion.change_delegacion'
    form_class = DelegacionForm
    template_name = 'crud/formulario.html'
    success_message = 'Delegación «%(nombre)s» modificada correctamente.'
    extra_context = {'titulo': 'Modificar delegación', 'volver_url': reverse_lazy('delegaciones:delegacion_list')}


class DelegacionDeleteView(DelegacionBase, EliminarSeguroMixin, DeleteView):
    permission_required = 'institucion.delete_delegacion'
    template_name = 'crud/confirmar_eliminar.html'
    context_object_name = 'objeto'
    mensaje_exito = 'Delegación eliminada correctamente.'
    mensaje_protegido = ('No se puede eliminar la delegación porque tiene solicitudes ciudadanas asociadas.')
    extra_context = {'titulo': 'Eliminar delegación', 'cancelar_url': reverse_lazy('delegaciones:delegacion_list')}


def contacto_delegaciones(request):
    """Vista pública (informativa)."""
    return render(request, 'delegaciones/contacto.html')
