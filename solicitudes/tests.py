from django.test import TestCase
from django.urls import reverse

from cuentas.perfiles import ADMINISTRADOR, ADMINISTRATIVO, SUPERVISOR
from cuentas.testing import CLAVE, crear_usuario
from institucion.models import Autoridad, Delegacion
from .models import SeguimientoSolicitud, Solicitud

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
