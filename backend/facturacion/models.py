# backend/facturacion/models.py
# Reemplaza el método save() de ItemFactura con este:

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from terceros.models import Tercero

class Factura(models.Model):
    """
    Representa el encabezado de una factura de venta.
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    cliente = models.ForeignKey(Tercero, on_delete=models.PROTECT, related_name='facturas')
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='borrador')
    cufe = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name="CUFE")
    qr_code = models.TextField(blank=True, null=True, verbose_name="Código QR")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def calcular_totales(self):
        """Recalcula los totales de la factura basándose en sus items"""
        subtotal = Decimal('0')
        impuestos = Decimal('0')
        
        for item in self.items.all():
            subtotal_item = item.cantidad * item.precio_unitario
            subtotal += subtotal_item
            if item.lleva_iva:
                impuestos += subtotal_item * Decimal('0.19')
        
        self.subtotal = subtotal
        self.impuestos = impuestos.quantize(Decimal('0.01'))
        self.total = subtotal + impuestos
        self.save()

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.nombre_razon_social}"

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_emision', '-id']

class ItemFactura(models.Model):
    """
    Representa una línea de producto o servicio dentro de una factura.
    """
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items')
    descripcion = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    lleva_iva = models.BooleanField(default=True, verbose_name="¿Lleva IVA?")
    subtotal_linea = models.DecimalField(max_digits=15, decimal_places=2, help_text="Subtotal antes de impuestos")

    def save(self, *args, **kwargs):
        # Calcular el subtotal de la línea antes de guardar
        self.subtotal_linea = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item: {self.descripcion} en Factura #{self.factura.id}"

    class Meta:
        verbose_name = "Ítem de Factura"
        verbose_name_plural = "Ítems de Factura"

# Signals para actualizar totales automáticamente
@receiver(post_save, sender=ItemFactura)
def actualizar_totales_factura_on_save(sender, instance, **kwargs):
    """Actualiza los totales cuando se guarda un item"""
    instance.factura.calcular_totales()

@receiver(post_delete, sender=ItemFactura)
def actualizar_totales_factura_on_delete(sender, instance, **kwargs):
    """Actualiza los totales cuando se elimina un item"""
    instance.factura.calcular_totales()