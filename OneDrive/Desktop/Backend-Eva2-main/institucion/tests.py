from django.test import TestCase
from django.urls import reverse

from cuentas.perfiles import ADMINISTRADOR, SUPERVISOR
from cuentas.testing import CLAVE, crear_usuario
from .models import Autoridad, Delegacion


class AutoridadCrudTests(TestCase):
    def setUp(self):
        crear_usuario(ADMINISTRADOR)
        crear_usuario(SUPERVISOR)
        self.client.login(username='administrador', password=CLAVE)

    def test_crear(self):
        r = self.client.post(reverse('institucion:autoridad_create'), {'nombre': 'Juan Pérez', 'cargo': 'Concejal', 'descripcion': ''})
        self.assertRedirects(r, reverse('institucion:autoridad_list'))
        self.assertTrue(Autoridad.objects.filter(nombre='Juan Pérez').exists())

    def test_validaciones(self):
        r = self.client.post(reverse('institucion:autoridad_create'), {'nombre': 'Juan', 'cargo': 'Concejal'})
        self.assertContains(r, 'al menos nombre y apellido')
        Autoridad.objects.create(nombre='Ana Soto', cargo='Alcaldesa')
        r = self.client.post(reverse('institucion:autoridad_create'), {'nombre': 'ana soto', 'cargo': 'alcaldesa'})
        self.assertContains(r, 'Ya existe una autoridad')

    def test_modificar_buscar_eliminar(self):
        a = Autoridad.objects.create(nombre='Ana Soto', cargo='Alcaldesa')
        self.client.post(reverse('institucion:autoridad_update', args=[a.pk]), {'nombre': 'Ana Soto Rojas', 'cargo': 'Alcaldesa'})
        a.refresh_from_db()
        self.assertEqual(a.nombre, 'Ana Soto Rojas')
        r = self.client.get(reverse('institucion:autoridad_list'), {'q': 'rojas'})
        self.assertContains(r, 'Ana Soto Rojas')
        r = self.client.get(reverse('institucion:autoridad_list'), {'q': 'zzz'})
        self.assertContains(r, 'No hay autoridades')
        self.client.post(reverse('institucion:autoridad_delete', args=[a.pk]))
        self.assertFalse(Autoridad.objects.filter(pk=a.pk).exists())

    def test_supervisor_no_puede_eliminar(self):
        a = Autoridad.objects.create(nombre='Ana Soto', cargo='Alcaldesa')
        self.client.login(username='supervisor', password=CLAVE)
        self.assertEqual(self.client.post(reverse('institucion:autoridad_delete', args=[a.pk])).status_code, 403)
        self.assertTrue(Autoridad.objects.filter(pk=a.pk).exists())

    def test_paginas_publicas_sin_botones_de_edicion(self):
        self.client.logout()
        Autoridad.objects.create(nombre='Ana Soto', cargo='Alcaldesa')
        r = self.client.get(reverse('institucion:inicio'))
        self.assertContains(r, 'Ana Soto')
        self.assertNotContains(r, 'Eliminar')
