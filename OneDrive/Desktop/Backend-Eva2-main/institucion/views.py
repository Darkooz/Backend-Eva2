from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from config.mixins import BuscadorMixin, EliminarSeguroMixin
from .forms import AutoridadForm
from .models import Autoridad


# ---------------------------------------------------------------------------
# Vistas públicas (información institucional)
# ---------------------------------------------------------------------------
def inicio(request):
    q = request.GET.get('q', '')
    autoridades = Autoridad.objects.select_related('delegacion').order_by('nombre')
    if q:
        autoridades = autoridades.filter(
            Q(nombre__icontains=q) | Q(cargo__icontains=q)
        )
    return render(request, 'institucion/inicio.html', {
        'autoridades': autoridades,
        'q': q,
    })


def historia(request):
    return render(request, 'institucion/historia.html')


# ---------------------------------------------------------------------------
# Mantenedor de Autoridades (requiere sesión + permisos del perfil)
# ---------------------------------------------------------------------------
class AutoridadBase(LoginRequiredMixin, PermissionRequiredMixin):
    model = Autoridad
    success_url = reverse_lazy('institucion:autoridad_list')


class AutoridadListView(AutoridadBase, BuscadorMixin, ListView):
    permission_required = 'institucion.view_autoridad'
    template_name = 'institucion/autoridad_list.html'
    context_object_name = 'autoridades'
    paginate_by = 8
    campos_busqueda = ('nombre', 'cargo', 'descripcion', 'delegacion__nombre')

    def get_queryset(self):
        return super().get_queryset().select_related('delegacion').order_by('nombre')


class AutoridadCreateView(AutoridadBase, SuccessMessageMixin, CreateView):
    permission_required = 'institucion.add_autoridad'
    form_class = AutoridadForm
    template_name = 'crud/formulario.html'
    success_message = 'Autoridad «%(nombre)s» creada correctamente.'
    extra_context = {'titulo': 'Nueva autoridad', 'volver_url': reverse_lazy('institucion:autoridad_list')}


class AutoridadUpdateView(AutoridadBase, SuccessMessageMixin, UpdateView):
    permission_required = 'institucion.change_autoridad'
    form_class = AutoridadForm
    template_name = 'crud/formulario.html'
    success_message = 'Autoridad «%(nombre)s» modificada correctamente.'
    extra_context = {'titulo': 'Modificar autoridad', 'volver_url': reverse_lazy('institucion:autoridad_list')}


class AutoridadDeleteView(AutoridadBase, EliminarSeguroMixin, DeleteView):
    permission_required = 'institucion.delete_autoridad'
    template_name = 'crud/confirmar_eliminar.html'
    context_object_name = 'objeto'
    mensaje_exito = 'Autoridad eliminada correctamente.'
    extra_context = {'titulo': 'Eliminar autoridad', 'cancelar_url': reverse_lazy('institucion:autoridad_list')}
