 #contabilidad/models.py

from django.db import models
from django.core.exceptions import ValidationError
from terceros.models import Tercero
from django.utils import timezone
from datetime import date



class Cuenta(models.Model):
    codigo = models.CharField(max_length=20, unique=True, primary_key=True, verbose_name="Código")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Cuenta")
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    def __str__(self): return f"{self.codigo} - {self.nombre}"
    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigo']

class AsientoContable(models.Model):
    fecha = models.DateField(verbose_name="Fecha del Asiento")

    # NUEVO: año/periodo fiscal (1..12 o 13)
    fiscal_year   = models.PositiveIntegerField(db_index=True, default=0)
    fiscal_period = models.PositiveSmallIntegerField(db_index=True, default=0)

    tercero = models.ForeignKey(Tercero, on_delete=models.PROTECT, verbose_name="Tercero Involucrado")
    concepto = models.CharField(max_length=500, verbose_name="Concepto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    descripcion_adicional = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=10, default="vigente", choices=[("vigente","Vigente"),("anulado","Anulado")])
    anulado_por = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    anulado_en = models.DateTimeField(null=True, blank=True)
    anulacion_motivo = models.TextField(blank=True, null=True)
    ajusta_a = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="ajustes")

    def save(self, *args, **kwargs):
        # Si no los envían, los derivamos de la fecha
        if not self.fiscal_year and self.fecha:
            self.fiscal_year = self.fecha.year
        if not self.fiscal_period and self.fecha:
            # por defecto, el mes real (1..12). El 13 sólo lo pondrás manualmente cuando corresponda.
            self.fiscal_period = self.fecha.month
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Asiento #{self.id} del {self.fecha} - {self.concepto}"

    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha', '-id']

class MovimientoContable(models.Model):
    asiento = models.ForeignKey(AsientoContable, on_delete=models.CASCADE, related_name='movimientos')
    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT)
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Débito")
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Crédito")
    def clean(self):
        if self.debito > 0 and self.credito > 0:
            raise ValidationError("Un movimiento no puede tener valor en Débito y Crédito simultáneamente.")
        if self.debito == 0 and self.credito == 0:
            raise ValidationError("El movimiento debe tener un valor en Débito o en Crédito.")
    def __str__(self):
        if self.debito > 0: return f"Débito a {self.cuenta.codigo} por {self.debito}"
        return f"Crédito a {self.cuenta.codigo} por {self.credito}"
    class Meta:
        verbose_name = "Movimiento Contable"
        verbose_name_plural = "Movimientos Contables"
        ordering = ['asiento', 'id']

# --- Periodo contable ---
class PeriodoContable(models.Model):
    ESTADOS = (('abierto','Abierto'),('cierre','En Cierre'),('cerrado','Cerrado'))
    anio = models.PositiveIntegerField(unique=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='abierto')
    ajustes_inicio = models.DateField()  # p.ej. Y+1-01-01
    ajustes_fin    = models.DateField()  # p.ej. Y+1-03-31
    habilitar_mes13 = models.BooleanField(default=True)
    requiere_pins_en_ajustes = models.BooleanField(default=True)

    def in_ajustes(self, d: date) -> bool:
        return self.ajustes_inicio <= d <= self.ajustes_fin

    @classmethod
    def ensure(cls, anio:int):
        obj, _ = cls.objects.get_or_create(
            anio=anio,
            defaults=dict(
                estado='abierto',
                ajustes_inicio=date(anio+1, 1, 1),
                ajustes_fin=date(anio+1, 3, 31),
                habilitar_mes13=True,
                requiere_pins_en_ajustes=True,
            )
        )
        return obj

    @classmethod
    def periodo_para_fecha(cls, d: date):
        return cls.ensure(d.year)

    @classmethod
    def activo_para_hoy(cls):
        hoy = timezone.localdate()
        return cls.ensure(hoy.year)