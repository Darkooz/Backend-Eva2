from .perfiles import COLOR_PERFIL, obtener_perfil


def perfil(request):
    """Expone el perfil del usuario y su color a todas las plantillas."""
    usuario = getattr(request, 'user', None)
    nombre = obtener_perfil(usuario)
    return {
        'perfil_usuario': nombre,
        'color_perfil': COLOR_PERFIL.get(nombre, 'secondary'),
    }
