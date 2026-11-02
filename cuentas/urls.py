from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm, NuevaClaveForm, RecuperarClaveForm

app_name = 'cuentas'

urlpatterns = [
    # Inicio / cierre de sesión
    path('login/', auth_views.LoginView.as_view(
        template_name='cuentas/login.html', authentication_form=LoginForm,
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # solo POST

    # Dashboards por perfil
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/administrador/', views.dashboard_administrador, name='dashboard_administrador'),
    path('panel/supervisor/', views.dashboard_supervisor, name='dashboard_supervisor'),
    path('panel/administrativo/', views.dashboard_administrativo, name='dashboard_administrativo'),

    # Recuperación de contraseña por correo (token seguro de Django)
    path('recuperar/', auth_views.PasswordResetView.as_view(
        template_name='cuentas/password_reset_form.html',
        form_class=RecuperarClaveForm,
        email_template_name='cuentas/emails/password_reset_email.txt',
        html_email_template_name='cuentas/emails/password_reset_email.html',
        subject_template_name='cuentas/emails/password_reset_subject.txt',
        success_url=reverse_lazy('cuentas:password_reset_done')), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='cuentas/password_reset_done.html'), name='password_reset_done'),
    path('recuperar/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='cuentas/password_reset_complete.html'), name='password_reset_complete'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='cuentas/password_reset_confirm.html',
        form_class=NuevaClaveForm,
        success_url=reverse_lazy('cuentas:password_reset_complete')), name='password_reset_confirm'),

    # Gestión de usuarios (Administrador)
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_delete'),
]
