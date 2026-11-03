"""Reglas para las evidencias adjuntas (PDF, JPG, PNG)."""
import os

from django.core.exceptions import ValidationError

MAX_BYTES = 5 * 1024 * 1024     # 5 MB por archivo
MAX_ARCHIVOS = 5                # por solicitud

# extensión permitida -> tipo real esperado
TIPOS_POR_EXTENSION = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
}


def detectar_tipo(cabecera):
    """Identifica el tipo real mirando los primeros bytes (no confía en la extensión)."""
    if cabecera.startswith(b'%PDF-'):
        return 'application/pdf'
    if cabecera.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if cabecera.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    return None


def validar_evidencia(archivo):
    """Valida extensión, tamaño y contenido. Devuelve el tipo real detectado."""
    nombre = os.path.basename(archivo.name)
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in TIPOS_POR_EXTENSION:
        raise ValidationError(f'«{nombre}»: formato no permitido. Solo se aceptan PDF, JPG o PNG.')
    if archivo.size == 0:
        raise ValidationError(f'«{nombre}»: el archivo está vacío.')
    if archivo.size > MAX_BYTES:
        raise ValidationError(f'«{nombre}»: supera el máximo de {MAX_BYTES // (1024 * 1024)} MB.')
    archivo.seek(0)
    cabecera = archivo.read(8)
    archivo.seek(0)
    tipo = detectar_tipo(cabecera)
    if tipo is None or tipo != TIPOS_POR_EXTENSION[extension]:
        raise ValidationError(f'«{nombre}»: el contenido no corresponde a un archivo {extension.upper()[1:]} válido.')
    return tipo
