from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .perfiles import obtener_perfil


def perfil_requerido(*perfiles):
    """Exige sesión iniciada y que el usuario pertenezca a alguno de los perfiles."""
    def decorador(vista):
        @login_required
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if obtener_perfil(request.user) not in perfiles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
