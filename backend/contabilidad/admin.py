from django.contrib import admin

# backend/contabilidad/admin.py
from django.contrib import admin
from .models import Cuenta, AsientoContable, MovimientoContable

class MovimientoContableInline(admin.TabularInline):
    """
    Inline para editar movimientos directamente desde el asiento
    """
    model = MovimientoContable
    extra = 2  # Muestra 2 líneas vacías por defecto
    fields = ['cuenta', 'debito', 'credito']

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el Plan de Cuentas
    """
    list_display = ['codigo', 'nombre', 'padre']
    list_filter = ['padre']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']

@admin.register(AsientoContable)
class AsientoContableAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Asientos Contables
    """
    list_display = ['id', 'fecha', 'concepto', 'tercero', 'get_total_debitos', 'get_total_creditos']
    list_filter = ['fecha', 'tercero']
    search_fields = ['concepto', 'descripcion', 'tercero__nombre_razon_social']
    date_hierarchy = 'fecha'
    inlines = [MovimientoContableInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('fecha', 'tercero', 'concepto', 'descripcion')
        }),
    )
    
    def get_total_debitos(self, obj):
        """Calcula el total de débitos del asiento"""
        total = sum(m.debito for m in obj.movimientos.all())
        return f"${total:,.2f}"
    get_total_debitos.short_description = 'Total Débitos'
    
    def get_total_creditos(self, obj):
        """Calcula el total de créditos del asiento"""
        total = sum(m.credito for m in obj.movimientos.all())
        return f"${total:,.2f}"
    get_total_creditos.short_description = 'Total Créditos'

@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Movimientos Contables
    """
    list_display = ['asiento', 'cuenta', 'debito', 'credito']
    list_filter = ['asiento__fecha', 'cuenta']
    search_fields = ['asiento__concepto', 'cuenta__nombre']