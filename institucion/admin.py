from django.contrib import admin
from .models import Delegacion, Autoridad

@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'encargado', 'direccion', 'telefono')
    search_fields = ('nombre', 'encargado', 'direccion')

@admin.register(Autoridad)
class AutoridadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'delegacion')
    list_filter = ('delegacion',)
    search_fields = ('nombre', 'cargo')