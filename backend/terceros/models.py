from django.db import models

class Tercero(models.Model):
    """
    Representa a una persona o empresa (cliente, proveedor, etc.) en el sistema.
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('NIT', 'NIT'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]

    tipo_documento = models.CharField(
        max_length=3,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name="Tipo de Documento"
    )
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Documento"
    )
    nombre_razon_social = models.CharField(
        max_length=255,
        verbose_name="Nombre o Razón Social"
    )
    direccion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Correo Electrónico"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_razon_social} ({self.tipo_documento} {self.numero_documento})"

    class Meta:
        verbose_name = "Tercero"
        verbose_name_plural = "Terceros"
        ordering = ['nombre_razon_social']