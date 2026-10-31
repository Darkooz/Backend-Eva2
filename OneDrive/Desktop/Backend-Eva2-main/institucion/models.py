from django.db import models

class Delegacion(models.Model):
    nombre = models.CharField(max_length=100)
    encargado = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Delegaciones'

    def __str__(self):
        return self.nombre

class Autoridad(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    delegacion = models.ForeignKey(
        Delegacion, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='autoridades'
    )
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Autoridades'

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"