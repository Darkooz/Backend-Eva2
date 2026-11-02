import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .perfiles import ADMINISTRADOR, ADMINISTRATIVO, SUPERVISOR
from .testing import CLAVE, crear_usuario

User = get_user_model()


class GruposTests(TestCase):
    def test_grupos_y_permisos_creados_por_migrate(self):
        for perfil in (ADMINISTRADOR, SUPERVISOR, ADMINISTRATIVO):
            self.assertTrue(Group.objects.filter(name=perfil).exists())
        admin = Group.objects.get(name=ADMINISTRADOR).permissions.values_list('codename', flat=True)
        sup = Group.objects.get(name=SUPERVISOR).permissions.values_list('codename', flat=True)
        adm = Group.objects.get(name=ADMINISTRATIVO).permissions.values_list('codename', flat=True)
        self.assertIn('delete_user', admin)
        self.assertNotIn('delete_autoridad', sup)
        self.assertIn('gestionar_solicitud', sup)
        self.assertNotIn('change_autoridad', adm)
        self.assertNotIn('gestionar_solicitud', adm)


class LoginTests(TestCase):
    def test_login_redirige_al_panel_de_su_perfil(self):
        destinos = {ADMINISTRADOR: 'dashboard_administrador', SUPERVISOR: 'dashboard_supervisor',
                    ADMINISTRATIVO: 'dashboard_administrativo'}
        for perfil, vista in destinos.items():
            crear_usuario(perfil)
            r = self.client.post(reverse('cuentas:login'), {'username': perfil.lower(), 'password': CLAVE}, follow=True)
            self.assertRedirects(r, reverse(f'cuentas:{vista}'))
            self.assertContains(r, f'Panel')
            self.client.post(reverse('cuentas:logout'))

    def test_credenciales_invalidas(self):
        crear_usuario(SUPERVISOR)
        r = self.client.post(reverse('cuentas:login'), {'username': 'supervisor', 'password': 'mala'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context['user'].is_authenticated)

    def test_logout_cierra_sesion(self):
        crear_usuario(SUPERVISOR)
        self.client.login(username='supervisor', password=CLAVE)
        self.client.post(reverse('cuentas:logout'))
        r = self.client.get(reverse('cuentas:dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_vistas_protegidas_exigen_login(self):
        for nombre in ('cuentas:dashboard', 'cuentas:usuario_list', 'institucion:autoridad_list',
                       'delegaciones:delegacion_list', 'solicitudes:solicitud_list', 'solicitudes:solicitud_create'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertIn(reverse('cuentas:login'), r.url)

    def test_admin_de_django_ya_no_esta_disponible(self):
        self.assertEqual(self.client.get('/admin/').status_code, 404)

    def test_paginas_publicas(self):
        for nombre in ('institucion:inicio', 'institucion:historia', 'delegaciones:contacto', 'cuentas:login'):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)


class RestriccionPorPerfilTests(TestCase):
    def setUp(self):
        for perfil in (ADMINISTRADOR, SUPERVISOR, ADMINISTRATIVO):
            crear_usuario(perfil)

    def _get(self, usuario, nombre):
        self.client.login(username=usuario, password=CLAVE)
        return self.client.get(reverse(nombre)).status_code

    def test_dashboards_cruzados_denegados(self):
        self.assertEqual(self._get('supervisor', 'cuentas:dashboard_administrador'), 403)
        self.assertEqual(self._get('administrativo', 'cuentas:dashboard_supervisor'), 403)
        self.assertEqual(self._get('administrador', 'cuentas:dashboard_supervisor'), 403)
        self.assertEqual(self._get('administrador', 'cuentas:dashboard_administrador'), 200)

    def test_gestion_de_usuarios_solo_administrador(self):
        self.assertEqual(self._get('administrador', 'cuentas:usuario_list'), 200)
        self.assertEqual(self._get('supervisor', 'cuentas:usuario_list'), 403)
        self.assertEqual(self._get('administrativo', 'cuentas:usuario_list'), 403)

    def test_crear_en_mantenedores(self):
        self.assertEqual(self._get('administrativo', 'institucion:autoridad_create'), 403)
        self.assertEqual(self._get('supervisor', 'institucion:autoridad_create'), 200)
        self.assertEqual(self._get('administrativo', 'delegaciones:delegacion_create'), 403)
        self.assertEqual(self._get('administrativo', 'institucion:autoridad_list'), 200)

    def test_botones_segun_perfil(self):
        self.client.login(username='administrativo', password=CLAVE)
        r = self.client.get(reverse('institucion:autoridad_list'))
        self.assertNotContains(r, '+ Agregar')
        self.client.login(username='administrador', password=CLAVE)
        r = self.client.get(reverse('institucion:autoridad_list'))
        self.assertContains(r, '+ Agregar')

    def test_usuario_sin_perfil_recibe_403_en_panel(self):
        User.objects.create_user('sinperfil', password=CLAVE)
        self.client.login(username='sinperfil', password=CLAVE)
        self.assertEqual(self.client.get(reverse('cuentas:dashboard')).status_code, 403)

    def test_superusuario_es_administrador(self):
        User.objects.create_superuser('root', 'root@muni.local', CLAVE)
        self.client.login(username='root', password=CLAVE)
        r = self.client.get(reverse('cuentas:dashboard'), follow=True)
        self.assertRedirects(r, reverse('cuentas:dashboard_administrador'))


class GestionUsuariosTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario(ADMINISTRADOR)
        self.client.login(username='administrador', password=CLAVE)

    def _datos(self, **extra):
        datos = {'username': 'nuevo', 'first_name': 'Nuevo', 'last_name': 'Usuario', 'email': 'nuevo@muni.cl',
                 'grupo': Group.objects.get(name=SUPERVISOR).pk, 'password1': 'Clave-Muy-Larga-77', 'password2': 'Clave-Muy-Larga-77'}
        datos.update(extra)
        return datos

    def test_crear_usuario_con_perfil(self):
        r = self.client.post(reverse('cuentas:usuario_create'), self._datos())
        self.assertRedirects(r, reverse('cuentas:usuario_list'))
        nuevo = User.objects.get(username='nuevo')
        self.assertEqual(list(nuevo.groups.values_list('name', flat=True)), [SUPERVISOR])
        self.assertTrue(self.client.login(username='nuevo', password='Clave-Muy-Larga-77'))

    def test_correo_duplicado_rechazado(self):
        r = self.client.post(reverse('cuentas:usuario_create'), self._datos(email='ADMINISTRADOR@muni.local'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevo').exists())

    def test_editar_cambia_perfil(self):
        u = crear_usuario(ADMINISTRATIVO)
        r = self.client.post(reverse('cuentas:usuario_update', args=[u.pk]), {
            'first_name': 'A', 'last_name': 'B', 'email': 'a@b.cl', 'is_active': 'on',
            'grupo': Group.objects.get(name=SUPERVISOR).pk})
        self.assertRedirects(r, reverse('cuentas:usuario_list'))
        self.assertEqual(list(u.groups.values_list('name', flat=True)), [SUPERVISOR])

    def test_no_puede_eliminarse_a_si_mismo(self):
        r = self.client.post(reverse('cuentas:usuario_delete', args=[self.admin.pk]))
        self.assertRedirects(r, reverse('cuentas:usuario_list'))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_eliminar_otro_usuario(self):
        u = crear_usuario(ADMINISTRATIVO)
        self.client.post(reverse('cuentas:usuario_delete', args=[u.pk]))
        self.assertFalse(User.objects.filter(pk=u.pk).exists())

    def test_busqueda(self):
        crear_usuario(SUPERVISOR)
        r = self.client.get(reverse('cuentas:usuario_list'), {'q': 'supervisor'})
        self.assertContains(r, 'supervisor')
        self.assertNotContains(r, '>administrativo<')


class RecuperarClaveTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario(SUPERVISOR)

    def _solicitar(self):
        r = self.client.post(reverse('cuentas:password_reset'), {'email': 'supervisor@muni.local'})
        self.assertRedirects(r, reverse('cuentas:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        return re.search(r'https?://[^\s]+/cuentas/recuperar/[^\s]+', mail.outbox[0].body).group(0)

    def test_flujo_completo(self):
        enlace = self._solicitar()                       # 1-3: solicitar, token, correo con enlace
        ruta = enlace.split('testserver')[1]
        r = self.client.get(ruta, follow=True)           # 4: validar token
        self.assertTrue(r.context['validlink'])
        r = self.client.post(r.request['PATH_INFO'], {   # 5: nueva contraseña
            'new_password1': 'Otra-Clave-Segura-88', 'new_password2': 'Otra-Clave-Segura-88'})
        self.assertRedirects(r, reverse('cuentas:password_reset_complete'))   # 6: confirmación
        self.assertTrue(self.client.login(username='supervisor', password='Otra-Clave-Segura-88'))
        self.assertFalse(self.client.login(username='supervisor', password=CLAVE))

    def test_token_de_un_solo_uso(self):
        ruta = self._solicitar().split('testserver')[1]
        r = self.client.get(ruta, follow=True)
        self.client.post(r.request['PATH_INFO'], {'new_password1': 'Otra-Clave-Segura-88', 'new_password2': 'Otra-Clave-Segura-88'})
        r = self.client.get(ruta, follow=True)
        self.assertFalse(r.context['validlink'])

    def test_token_invalido(self):
        r = self.client.get(reverse('cuentas:password_reset_confirm', args=['Mg', 'abc-123']), follow=True)
        self.assertFalse(r.context['validlink'])
        self.assertContains(r, 'Enlace inválido')

    def test_correo_inexistente_no_revela_informacion(self):
        r = self.client.post(reverse('cuentas:password_reset'), {'email': 'nadie@x.cl'})
        self.assertRedirects(r, reverse('cuentas:password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_claves_distintas_rechazadas(self):
        ruta = self._solicitar().split('testserver')[1]
        r = self.client.get(ruta, follow=True)
        r = self.client.post(r.request['PATH_INFO'], {'new_password1': 'Otra-Clave-Segura-88', 'new_password2': 'distinta'})
        self.assertEqual(r.status_code, 200)
