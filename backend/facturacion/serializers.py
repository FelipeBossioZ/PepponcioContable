from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Factura, ItemFactura

# Tasa de IVA estándar en Colombia
IVA_RATE = Decimal('0.19')

class ItemFacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemFactura
        fields = ['id', 'descripcion', 'cantidad', 'precio_unitario', 'lleva_iva', 'subtotal_linea']
        read_only_fields = ['id', 'subtotal_linea']

class FacturaSerializer(serializers.ModelSerializer):
    items = ItemFacturaSerializer(many=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_razon_social', read_only=True)

    class Meta:
        model = Factura
        fields = [
            'id', 'cliente', 'cliente_nombre', 'fecha_emision', 'fecha_vencimiento',
            'subtotal', 'impuestos', 'total', 'estado', 'cufe', 'qr_code', 'items'
        ]
        read_only_fields = ['id', 'subtotal', 'impuestos', 'total', 'cufe', 'qr_code', 'cliente_nombre']

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        with transaction.atomic():
            factura = Factura.objects.create(**validated_data)
            subtotal_factura = Decimal('0.00')
            impuestos_factura = Decimal('0.00')

            for item_data in items_data:
                item = ItemFactura.objects.create(factura=factura, **item_data)
                subtotal_factura += item.subtotal_linea
                if item.lleva_iva:
                    impuestos_factura += item.subtotal_linea * IVA_RATE

            # Actualizar los totales de la factura
            factura.subtotal = subtotal_factura
            factura.impuestos = impuestos_factura.quantize(Decimal('0.01'))
            factura.total = subtotal_factura + impuestos_factura
            factura.save()

        return factura