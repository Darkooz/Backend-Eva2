import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.perfiles import ADMINISTRADOR, ADMINISTRATIVO, SUPERVISOR
from cuentas.testing import CLAVE, crear_usuario
from institucion.models import Autoridad, Delegacion
from .archivos import MAX_BYTES
from .models import AdjuntoSeguimiento, SeguimientoSolicitud, Solicitud

E = Solicitud.Estado


class TransaccionTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario(ADMINISTRADOR)
        self.sup = crear_usuario(SUPERVISOR)
        self.administrativo = crear_usuario(ADMINISTRATIVO)
        self.delegacion = Delegacion.objects.create(nombre='Centro', direccion='Cienfuegos 226')
        self.autoridad = Autoridad.objects.create(nombre='Ana Soto', cargo='Alcaldesa')
        self.datos = {'solicitante_nombre': 'María López', 'solicitante_email': 'maria@correo.cl', 'solicitante_telefono': '',
                      'tipo': 'alumbrado', 'prioridad': 'alta', 'delegacion': self.delegacion.pk,
                      'descripcion': 'Poste sin luz hace una semana en la esquina.'}

    def _registrar(self):
        self.client.login(username='administrativo', password=CLAVE)
        r = self.client.post(reverse('solicitudes:solicitud_create'), self.datos)
        s = Solicitud.objects.get()
        self.assertRedirects(r, reverse('solicitudes:solicitud_detail', args=[s.pk]))
        return s

    def test_registro_crea_solicitud_e_historial(self):
        s = self._registrar()
        self.assertEqual(s.estado, E.PENDIENTE)
        self.assertEqual(s.creada_por, self.administrativo)
        self.assertEqual(s.seguimientos.count(), 1)

    def test_validaciones_de_registro(self):
        self.client.login(username='administrativo', password=CLAVE)
        malo = dict(self.datos, descripcion='corta', solicitante_nombre='María', solicitante_email='')
        r = self.client.post(reverse('solicitudes:solicitud_create'), malo)
        self.assertContains(r, 'al menos 15 caracteres')
        self.assertContains(r, 'nombre y apellido')
        self.assertContains(r, 'medio de contacto')
        self.assertEqual(Solicitud.objects.count(), 0)

    def test_flujo_completo_y_cierre(self):
        s = self._registrar()
        self.client.login(username='supervisor', password=CLAVE)
        url = reverse('solicitudes:solicitud_detail', args=[s.pk])
        # En proceso sin autoridad: rechazado
        r = self.client.post(url, {'estado': E.EN_PROCESO, 'autoridad': '', 'comentario': ''})
        self.assertContains(r, 'Debe asignar una autoridad')
        # Resolver directamente desde pendiente: transición no permitida
        r = self.client.post(url, {'estado': E.RESUELTA, 'autoridad': self.autoridad.pk, 'comentario': 'x'})
        self.assertContains(r, 'no es una de las opciones disponibles')
        # En proceso con autoridad
        self.client.post(url, {'estado': E.EN_PROCESO, 'autoridad': self.autoridad.pk, 'comentario': 'Se envía cuadrilla'})
        s.refresh_from_db()
        self.assertEqual((s.estado, s.autoridad), (E.EN_PROCESO, self.autoridad))
        # Resolver sin comentario: rechazado
        r = self.client.post(url, {'estado': E.RESUELTA, 'autoridad': self.autoridad.pk, 'comentario': ''})
        self.assertContains(r, 'Debe indicar un comentario')
        # Resolver correctamente
        self.client.post(url, {'estado': E.RESUELTA, 'autoridad': self.autoridad.pk, 'comentario': 'Luminaria reparada'})
        s.refresh_from_db()
        self.assertEqual(s.estado, E.RESUELTA)
        self.assertEqual(SeguimientoSolicitud.objects.filter(solicitud=s).count(), 3)
        # Cerrada: ya no se modifica
        r = self.client.post(url, {'estado': E.EN_PROCESO, 'autoridad': self.autoridad.pk, 'comentario': 'x'}, follow=True)
        self.assertContains(r, 'ya está cerrada')
        s.refresh_from_db()
        self.assertEqual(s.estado, E.RESUELTA)

    def test_sin_cambios_rechazado(self):
        s = self._registrar()
        self.client.login(username='supervisor', password=CLAVE)
        r = self.client.post(reverse('solicitudes:solicitud_detail', args=[s.pk]), {'estado': E.PENDIENTE, 'autoridad': '', 'comentario': ''})
        self.assertContains(r, 'No hay cambios')

    def test_administrativo_no_puede_gestionar_ni_eliminar(self):
        s = self._registrar()  # queda logueado como administrativo
        url = reverse('solicitudes:solicitud_detail', args=[s.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {'estado': E.EN_PROCESO, 'autoridad': self.autoridad.pk}).status_code, 403)
        self.assertEqual(self.client.post(reverse('solicitudes:solicitud_delete', args=[s.pk])).status_code, 403)

    def test_supervisor_no_elimina_pero_admin_si(self):
        s = self._registrar()
        self.client.login(username='supervisor', password=CLAVE)
        self.assertEqual(self.client.post(reverse('solicitudes:solicitud_delete', args=[s.pk])).status_code, 403)
        self.client.login(username='administrador', password=CLAVE)
        self.client.post(reverse('solicitudes:solicitud_delete', args=[s.pk]))
        self.assertEqual(Solicitud.objects.count(), 0)
        self.assertEqual(SeguimientoSolicitud.objects.count(), 0)

    def test_filtros_del_listado(self):
        self._registrar()
        r = self.client.get(reverse('solicitudes:solicitud_list'), {'estado': 'resuelta'})
        self.assertContains(r, 'No hay solicitudes')
        r = self.client.get(reverse('solicitudes:solicitud_list'), {'estado': 'pendiente', 'delegacion': self.delegacion.pk, 'q': 'lópez'})
        self.assertContains(r, 'María López')

    def test_dashboards_con_datos(self):
        self._registrar()
        for usuario, vista in (('administrador', 'administrador'), ('supervisor', 'supervisor'), ('administrativo', 'administrativo')):
            self.client.login(username=usuario, password=CLAVE)
            r = self.client.get(reverse(f'cuentas:dashboard_{vista}'))
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, 'Centro')  # delegación de la solicitud visible en cada panel
            if usuario != 'supervisor':
                self.assertContains(r, 'María López')


PDF = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 40
JPG = b'\xff\xd8\xff\xe0' + b'\x00' * 40

_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_MEDIA)
class EvidenciasTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA, ignore_errors=True)

    def setUp(self):
        crear_usuario(ADMINISTRADOR)
        crear_usuario(ADMINISTRATIVO)
        self.delegacion = Delegacion.objects.create(nombre='Centro', direccion='Cienfuegos 226')
        self.datos = {'solicitante_nombre': 'María López', 'solicitante_email': 'maria@correo.cl',
                      'tipo': 'alumbrado', 'prioridad': 'alta', 'delegacion': self.delegacion.pk,
                      'descripcion': 'Poste sin luz hace una semana en la esquina.'}
        self.client.login(username='administrativo', password=CLAVE)
        self.url = reverse('solicitudes:solicitud_create')

    def _post(self, *archivos):
        return self.client.post(self.url, dict(self.datos, evidencias=list(archivos)))

    def test_registro_con_pdf_y_imagen(self):
        r = self._post(SimpleUploadedFile('informe.pdf', PDF), SimpleUploadedFile('foto.png', PNG))
        s = Solicitud.objects.get()
        self.assertRedirects(r, reverse('solicitudes:solicitud_detail', args=[s.pk]))
        adjuntos = AdjuntoSeguimiento.objects.all()
        self.assertEqual(adjuntos.count(), 2)
        primero = s.seguimientos.first()
        self.assertEqual(set(a.seguimiento for a in adjuntos), {primero})
        self.assertEqual({a.tipo for a in adjuntos}, {'application/pdf', 'image/png'})
        for a in adjuntos:
            self.assertTrue(Path(a.archivo.path).exists())
            self.assertNotIn(a.nombre_original.split('.')[0], a.archivo.name)  # nombre aleatorio
        self.assertContains(self.client.get(reverse('solicitudes:solicitud_detail', args=[s.pk])), 'informe.pdf')

    def test_sin_evidencias_sigue_funcionando(self):
        self._post()
        self.assertEqual(Solicitud.objects.count(), 1)
        self.assertEqual(AdjuntoSeguimiento.objects.count(), 0)

    def test_rechaza_extension_no_permitida(self):
        r = self._post(SimpleUploadedFile('virus.exe', b'MZ' + b'0' * 20))
        self.assertContains(r, 'formato no permitido')
        self.assertEqual(Solicitud.objects.count(), 0)

    def test_rechaza_contenido_falso(self):
        r = self._post(SimpleUploadedFile('falso.pdf', b'esto no es un pdf'))
        self.assertContains(r, 'no corresponde a un archivo PDF')
        r = self._post(SimpleUploadedFile('truco.png', PDF))
        self.assertContains(r, 'no corresponde a un archivo PNG')
        self.assertEqual(Solicitud.objects.count(), 0)

    def test_rechaza_archivo_muy_grande_y_vacio(self):
        r = self._post(SimpleUploadedFile('grande.pdf', PDF + b'0' * MAX_BYTES))
        self.assertContains(r, 'supera el máximo')
        r = self._post(SimpleUploadedFile('vacio.png', b''))
        self.assertEqual(Solicitud.objects.count(), 0)

    def test_rechaza_demasiados_archivos(self):
        archivos = [SimpleUploadedFile(f'f{i}.jpg', JPG) for i in range(6)]
        r = self._post(*archivos)
        self.assertContains(r, 'como máximo 5 archivos')
        self.assertEqual(Solicitud.objects.count(), 0)

    def test_descarga_requiere_sesion(self):
        self._post(SimpleUploadedFile('informe.pdf', PDF))
        a = AdjuntoSeguimiento.objects.get()
        url = reverse('solicitudes:adjunto_descargar', args=[a.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertEqual(b''.join(r.streaming_content), PDF)
        self.client.logout()
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('cuentas:login'), r.url)

    def test_usuario_sin_permiso_no_descarga(self):
        self._post(SimpleUploadedFile('informe.pdf', PDF))
        a = AdjuntoSeguimiento.objects.get()
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_user('sinperfil', password=CLAVE)
        self.client.login(username='sinperfil', password=CLAVE)
        self.assertEqual(self.client.get(reverse('solicitudes:adjunto_descargar', args=[a.pk])).status_code, 403)

    def test_eliminar_solicitud_borra_los_archivos(self):
        self._post(SimpleUploadedFile('informe.pdf', PDF), SimpleUploadedFile('foto.jpg', JPG))
        rutas = [Path(a.archivo.path) for a in AdjuntoSeguimiento.objects.all()]
        self.assertTrue(all(r.exists() for r in rutas))
        s = Solicitud.objects.get()
        self.client.login(username='administrador', password=CLAVE)
        self.client.post(reverse('solicitudes:solicitud_delete', args=[s.pk]))
        self.assertEqual(AdjuntoSeguimiento.objects.count(), 0)
        self.assertFalse(any(r.exists() for r in rutas))
