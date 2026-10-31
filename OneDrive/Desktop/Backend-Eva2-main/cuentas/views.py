from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from config.mixins import BuscadorMixin, EliminarSeguroMixin
from institucion.models import Autoridad, Delegacion
from solicitudes.models import SeguimientoSolicitud, Solicitud
from solicitudes.services import resumen_por_estado
from .decorators import perfil_requerido
from .forms import UsuarioCrearForm, UsuarioEditarForm
from .perfiles import ADMINISTRADOR, ADMINISTRATIVO, PERFILES, SUPERVISOR, obtener_perfil

User = get_user_model()

RUTA_DASHBOARD = {
    ADMINISTRADOR: 'cuentas:dashboard_administrador',
    SUPERVISOR: 'cuentas:dashboard_supervisor',
    ADMINISTRATIVO: 'cuentas:dashboard_administrativo',
}


# ---------------------------------------------------------------------------
# Dashboards: un panel distinto por perfil
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    """Redirige al panel que corresponde al perfil del usuario autenticado."""
    perfil = obtener_perfil(request.user)
    if perfil is None:
        raise PermissionDenied  # usuario sin perfil asignado
    return redirect(RUTA_DASHBOARD[perfil])


@perfil_requerido(ADMINISTRADOR)
def dashboard_administrador(request):
    """Visión global: usuarios, mantenedores y todas las transacciones."""
    contexto = {
        'total_usuarios': User.objects.count(),
        'perfiles': Group.objects.filter(name__in=PERFILES).annotate(total=Count('user')).order_by('name'),
        'total_delegaciones': Delegacion.objects.count(),
        'total_autoridades': Autoridad.objects.count(),
        'total_solicitudes': Solicitud.objects.count(),
        'resumen_estados': resumen_por_estado(),
        'ultimas_solicitudes': Solicitud.objects.select_related('delegacion')[:6],
        'ultimos_movimientos': SeguimientoSolicitud.objects.select_related('solicitud', 'usuario').order_by('-fecha', '-id')[:6],
    }
    return render(request, 'cuentas/dashboard_administrador.html', contexto)


@perfil_requerido(SUPERVISOR)
def dashboard_supervisor(request):
    """Información operacional: cola de trabajo y carga por delegación."""
    por_delegacion = Delegacion.objects.annotate(
        total=Count('solicitudes', distinct=True),
        pendientes=Count('solicitudes', filter=Q(solicitudes__estado=Solicitud.Estado.PENDIENTE), distinct=True),
    ).order_by('-pendientes', 'nombre')
    contexto = {
        'resumen_estados': resumen_por_estado(),
        'pendientes': Solicitud.objects.filter(estado=Solicitud.Estado.PENDIENTE).select_related('delegacion').order_by('fecha_creacion')[:6],
        'en_proceso': Solicitud.objects.filter(estado=Solicitud.Estado.EN_PROCESO).select_related('delegacion', 'autoridad')[:6],
        'por_delegacion': por_delegacion,
    }
    return render(request, 'cuentas/dashboard_supervisor.html', contexto)


@perfil_requerido(ADMINISTRATIVO)
def dashboard_administrativo(request):
    """Acceso acotado: consulta y registro de las propias solicitudes."""
    mias = Solicitud.objects.filter(creada_por=request.user)
    contexto = {
        'mis_solicitudes': mias.select_related('delegacion')[:8],
        'total_mias': mias.count(),
        'mis_pendientes': mias.filter(estado=Solicitud.Estado.PENDIENTE).count(),
    }
    return render(request, 'cuentas/dashboard_administrativo.html', contexto)


# ---------------------------------------------------------------------------
# Gestión de usuarios (solo Administrador: permisos auth.*_user)
# ---------------------------------------------------------------------------
class UsuarioBase(LoginRequiredMixin, PermissionRequiredMixin):
    model = User
    success_url = reverse_lazy('cuentas:usuario_list')


class UsuarioListView(UsuarioBase, BuscadorMixin, ListView):
    permission_required = 'auth.view_user'
    template_name = 'cuentas/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 10
    campos_busqueda = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self):
        return super().get_queryset().prefetch_related('groups').order_by('username')


class UsuarioCreateView(UsuarioBase, SuccessMessageMixin, CreateView):
    permission_required = 'auth.add_user'
    form_class = UsuarioCrearForm
    template_name = 'crud/formulario.html'
    success_message = 'Usuario «%(username)s» creado correctamente.'
    extra_context = {'titulo': 'Nuevo usuario', 'volver_url': reverse_lazy('cuentas:usuario_list')}


class UsuarioUpdateView(UsuarioBase, SuccessMessageMixin, UpdateView):
    permission_required = 'auth.change_user'
    form_class = UsuarioEditarForm
    template_name = 'crud/formulario.html'
    success_message = 'Usuario modificado correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['usuario_actual'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['titulo'] = f'Modificar usuario «{self.object.username}»'
        contexto['volver_url'] = reverse_lazy('cuentas:usuario_list')
        return contexto


class UsuarioDeleteView(UsuarioBase, EliminarSeguroMixin, DeleteView):
    permission_required = 'auth.delete_user'
    template_name = 'crud/confirmar_eliminar.html'
    context_object_name = 'objeto'
    mensaje_exito = 'Usuario eliminado correctamente.'
    extra_context = {
        'titulo': 'Eliminar usuario',
        'cancelar_url': reverse_lazy('cuentas:usuario_list'),
        'advertencia': 'Las solicitudes que registró se conservarán, pero sin autor asociado.',
    }

    def _motivo_bloqueo(self):
        if self.object == self.request.user:
            return 'No puede eliminar su propia cuenta.'
        if self.object.is_superuser and not self.request.user.is_superuser:
            return 'Solo un superusuario puede eliminar a otro superusuario.'
        return None

    # Se sobreescriben get/post (y no dispatch) para no saltarse la validación de permisos
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        motivo = self._motivo_bloqueo()
        if motivo:
            messages.error(request, motivo)
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        motivo = self._motivo_bloqueo()
        if motivo:
            messages.error(request, motivo)
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)
