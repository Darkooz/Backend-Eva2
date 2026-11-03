from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from config.mixins import BuscadorMixin, EliminarSeguroMixin
from institucion.models import Delegacion
from .forms import GestionSolicitudForm, SolicitudForm
from .models import AdjuntoSeguimiento, Solicitud
from .services import gestionar_solicitud, registrar_solicitud


class SolicitudBase(LoginRequiredMixin, PermissionRequiredMixin):
    model = Solicitud


class SolicitudListView(SolicitudBase, BuscadorMixin, ListView):
    permission_required = 'solicitudes.view_solicitud'
    template_name = 'solicitudes/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 10
    campos_busqueda = ('solicitante_nombre', 'descripcion', 'delegacion__nombre', 'autoridad__nombre')

    def get_queryset(self):
        queryset = super().get_queryset().select_related('delegacion', 'autoridad', 'creada_por')
        estado = self.request.GET.get('estado', '')
        delegacion = self.request.GET.get('delegacion', '')
        if estado in Solicitud.Estado.values:
            queryset = queryset.filter(estado=estado)
        if delegacion.isdigit():
            queryset = queryset.filter(delegacion_id=delegacion)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['estados'] = Solicitud.Estado.choices
        contexto['delegaciones'] = Delegacion.objects.order_by('nombre')
        contexto['estado_sel'] = self.request.GET.get('estado', '')
        contexto['delegacion_sel'] = self.request.GET.get('delegacion', '')
        return contexto


class SolicitudCreateView(SolicitudBase, CreateView):
    permission_required = 'solicitudes.add_solicitud'
    form_class = SolicitudForm
    template_name = 'crud/formulario.html'
    extra_context = {
        'titulo': 'Registrar solicitud ciudadana',
        'subtitulo': 'La solicitud quedará en estado Pendiente hasta que un supervisor la gestione.',
        'volver_url': reverse_lazy('solicitudes:solicitud_list'),
        'texto_boton': 'Registrar solicitud',
    }

    def form_valid(self, form):
        self.object = registrar_solicitud(form, self.request.user)
        messages.success(self.request, f'Solicitud #{self.object.pk} registrada correctamente.')
        return redirect('solicitudes:solicitud_detail', pk=self.object.pk)


class SolicitudDetailView(SolicitudBase, DetailView):
    permission_required = 'solicitudes.view_solicitud'
    template_name = 'solicitudes/solicitud_detail.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        return super().get_queryset().select_related('delegacion', 'autoridad', 'creada_por')

    def _puede_gestionar(self):
        return (self.request.user.has_perm('solicitudes.gestionar_solicitud')
                and not self.object.esta_cerrada)

    def get_context_data(self, form=None, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['seguimientos'] = self.object.seguimientos.select_related('usuario', 'autoridad').prefetch_related('adjuntos')
        contexto['puede_gestionar'] = self._puede_gestionar()
        if contexto['puede_gestionar']:
            contexto['form'] = form or GestionSolicitudForm(solicitud=self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm('solicitudes.gestionar_solicitud'):
            raise PermissionDenied
        if self.object.esta_cerrada:
            messages.error(request, 'La solicitud ya está cerrada y no admite modificaciones.')
            return redirect('solicitudes:solicitud_detail', pk=self.object.pk)
        form = GestionSolicitudForm(request.POST, solicitud=self.object)
        if form.is_valid():
            try:
                gestionar_solicitud(
                    self.object.pk, form.cleaned_data['estado'], form.cleaned_data['autoridad'],
                    form.cleaned_data['comentario'], request.user,
                )
            except ValidationError as error:
                messages.error(request, error.messages[0])
            else:
                messages.success(request, 'La solicitud fue actualizada y el cambio quedó registrado en el historial.')
            return redirect('solicitudes:solicitud_detail', pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form))


class SolicitudDeleteView(SolicitudBase, EliminarSeguroMixin, DeleteView):
    permission_required = 'solicitudes.delete_solicitud'
    template_name = 'crud/confirmar_eliminar.html'
    context_object_name = 'objeto'
    success_url = reverse_lazy('solicitudes:solicitud_list')
    mensaje_exito = 'Solicitud eliminada correctamente.'
    extra_context = {
        'titulo': 'Eliminar solicitud',
        'cancelar_url': reverse_lazy('solicitudes:solicitud_list'),
        'advertencia': 'También se eliminará todo su historial de seguimiento.',
    }


@login_required
def adjunto_descargar(request, pk):
    """Entrega una evidencia solo a usuarios con sesión y permiso para ver solicitudes."""
    if not request.user.has_perm('solicitudes.view_solicitud'):
        raise PermissionDenied
    adjunto = get_object_or_404(AdjuntoSeguimiento, pk=pk)
    try:
        archivo = adjunto.archivo.open('rb')
    except FileNotFoundError:
        raise Http404('El archivo ya no está disponible.')
    return FileResponse(archivo, content_type=adjunto.tipo, as_attachment=False,
                        filename=adjunto.nombre_original)
