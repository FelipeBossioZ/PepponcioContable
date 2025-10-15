from django.db import models
from django.core.exceptions import ValidationError
from terceros.models import Tercero

class Cuenta(models.Model):
    """
    Representa una cuenta del Plan Único de Cuentas (PUC).
    """
    codigo = models.CharField(max_length=20, unique=True, primary_key=True, verbose_name="Código")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Cuenta")
    # El campo 'padre' permite crear la estructura jerárquica del PUC
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigo']

class AsientoContable(models.Model):
    """
    Representa una transacción contable completa (el comprobante).
    Agrupa varios movimientos de débito y crédito.
    """
    fecha = models.DateField(verbose_name="Fecha del Asiento")
    tercero = models.ForeignKey(Tercero, on_delete=models.PROTECT, verbose_name="Tercero Involucrado")
    concepto = models.CharField(max_length=500, verbose_name="Concepto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def clean(self):
        # Este método se llamará antes de guardar para validar la lógica del modelo
        super().clean()

        # Después de que el asiento y sus movimientos se hayan guardado,
        # se debería verificar que la suma de débitos es igual a la de créditos.
        # Esta validación se hará a nivel de la API al momento de crear el asiento.

    def __str__(self):
        return f"Asiento #{self.id} del {self.fecha} - {self.concepto}"

    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha', '-id']

class MovimientoContable(models.Model):
    """
    Representa una línea individual dentro de un Asiento Contable (débito o crédito).
    """
    asiento = models.ForeignKey(AsientoContable, on_delete=models.CASCADE, related_name='movimientos')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT)
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Débito")
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Crédito")

    def clean(self):
        # Valida que un movimiento no puede tener débito y crédito al mismo tiempo
        if self.debito > 0 and self.credito > 0:
            raise ValidationError("Un movimiento no puede tener valor en Débito y Crédito simultáneamente.")
        if self.debito == 0 and self.credito == 0:
            raise ValidationError("El movimiento debe tener un valor en Débito o en Crédito.")

    def __str__(self):
        if self.debito > 0:
            return f"Débito a {self.cuenta.codigo} por {self.debito}"
        else:
            return f"Crédito a {self.cuenta.codigo} por {self.credito}"

    class Meta:
        verbose_name = "Movimiento Contable"
        verbose_name_plural = "Movimientos Contables"
        ordering = ['asiento', 'id']