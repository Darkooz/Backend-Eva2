ADMINISTRADOR = 'Administrador'
SUPERVISOR = 'Supervisor'
ADMINISTRATIVO = 'Administrativo'

PERFILES = (ADMINISTRADOR, SUPERVISOR, ADMINISTRATIVO)

# Color Bootstrap asociado a cada perfil (navbar, dashboards, insignias)
COLOR_PERFIL = {
    ADMINISTRADOR: 'danger',
    SUPERVISOR: 'primary',
    ADMINISTRATIVO: 'success',
}


def obtener_perfil(user):
    """Devuelve el perfil del usuario (nombre del grupo) o None.
    Un superusuario siempre se considera Administrador."""
    if user is None or not user.is_authenticated:
        return None
    if not hasattr(user, '_perfil_cache'):
        perfil = None
        if user.is_superuser:
            perfil = ADMINISTRADOR
        else:
            grupos = set(user.groups.values_list('name', flat=True))
            perfil = next((p for p in PERFILES if p in grupos), None)
        user._perfil_cache = perfil
    return user._perfil_cache
