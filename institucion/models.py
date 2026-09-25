from django.db import models

class Delegacion(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Autoridad(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    # Llave foránea para relacionar cada autoridad con una delegación
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE, related_name='autoridades')
    descripcion = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.nombre} - {self.cargo}"