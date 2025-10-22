 #contabilidad/models.py

from django.db import models
from django.core.exceptions import ValidationError
from terceros.models import Tercero
from django.utils import timezone

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
    descripcion_adicional = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    # backend/contabilidad/models.py (AsientoContable)
    estado = models.CharField(max_length=10, default="vigente", choices=[("vigente","Vigente"),("anulado","Anulado")])
    anulado_por = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    anulado_en = models.DateTimeField(null=True, blank=True)
    anulacion_motivo = models.TextField(blank=True, null=True)
    ajusta_a = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="ajustes")  # asiento de ajuste que anuló este

    






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

# --- Periodo contable ---
class PeriodoContable(models.Model):
    """
    Define el estado del periodo contable de un año.
    - estado: abierto/cerrado
    - ventana_enero_marzo: si True, permite anulación con PINs del 01/01 al 31/03 del año siguiente.
    """
    ANIO_ACTUAL = timezone.now().year  # referencia por defecto

    anio = models.PositiveIntegerField(unique=True)
    estado = models.CharField(max_length=10, choices=[("abierto","Abierto"),("cerrado","Cerrado")], default="abierto")
    ventana_enero_marzo = models.BooleanField(default=True)

    cerrado_por = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cerrado_en = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Periodo Contable"
        verbose_name_plural = "Periodos Contables"
        ordering = ["-anio"]

    def __str__(self):
        return f"Periodo {self.anio} — {self.estado.capitalize()}"

    @classmethod
    def periodo_para_fecha(cls, fecha):
        """devuelve (periodo, creado_si_no_existe) para el año de 'fecha'"""
        obj, _ = cls.objects.get_or_create(anio=fecha.year, defaults={"estado": "abierto"})
        return obj

    @classmethod
    def activo_para_hoy(cls):
        today = timezone.localdate()
        return cls.periodo_para_fecha(today)
