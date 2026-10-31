from django.test import TestCase
from django.urls import reverse

from cuentas.perfiles import ADMINISTRADOR
from cuentas.testing import CLAVE, crear_usuario
from institucion.models import Delegacion
from solicitudes.models import Solicitud


class DelegacionCrudTests(TestCase):
    def setUp(self):
        crear_usuario(ADMINISTRADOR)
        self.client.login(username='administrador', password=CLAVE)

    def test_crud_completo(self):
        r = self.client.post(reverse('delegaciones:delegacion_create'),
                             {'nombre': 'Centro', 'direccion': 'Cienfuegos 226', 'telefono': '512 207861', 'encargado': 'Alan'})
        self.assertRedirects(r, reverse('delegaciones:delegacion_list'))
        d = Delegacion.objects.get(nombre='Centro')
        self.client.post(reverse('delegaciones:delegacion_update', args=[d.pk]),
                         {'nombre': 'Centro Histórico', 'direccion': 'Cienfuegos 226'})
        d.refresh_from_db()
        self.assertEqual(d.nombre, 'Centro Histórico')
        self.assertContains(self.client.get(reverse('delegaciones:delegacion_list'), {'q': 'histórico'}), 'Centro Histórico')
        self.client.post(reverse('delegaciones:delegacion_delete', args=[d.pk]))
        self.assertFalse(Delegacion.objects.filter(pk=d.pk).exists())

    def test_validaciones(self):
        Delegacion.objects.create(nombre='Centro', direccion='x')
        r = self.client.post(reverse('delegaciones:delegacion_create'), {'nombre': 'CENTRO', 'direccion': 'y'})
        self.assertContains(r, 'Ya existe una delegación')
        r = self.client.post(reverse('delegaciones:delegacion_create'), {'nombre': 'Otra', 'direccion': 'y', 'telefono': 'abc'})
        self.assertContains(r, 'teléfono válido')

    def test_no_elimina_delegacion_con_solicitudes(self):
        d = Delegacion.objects.create(nombre='Centro', direccion='x')
        Solicitud.objects.create(solicitante_nombre='A B', tipo='aseo', descripcion='x' * 20, delegacion=d)
        r = self.client.post(reverse('delegaciones:delegacion_delete', args=[d.pk]), follow=True)
        self.assertContains(r, 'tiene solicitudes ciudadanas asociadas')
        self.assertTrue(Delegacion.objects.filter(pk=d.pk).exists())
