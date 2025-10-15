from rest_framework import serializers
from .models import Cuenta, AsientoContable, MovimientoContable
from django.db import transaction

class CuentaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Cuenta.
    Convierte los objetos de Cuenta a formato JSON y viceversa.
    """
    class Meta:
        model = Cuenta
        fields = ['codigo', 'nombre', 'padre']

class MovimientoContableSerializer(serializers.ModelSerializer):
    """
    Serializer para los movimientos contables individuales (líneas de un asiento).
    """
    class Meta:
        model = MovimientoContable
        fields = ['cuenta', 'debito', 'credito']

class AsientoContableSerializer(serializers.ModelSerializer):
    """
    Serializer para el Asiento Contable.
    Maneja la creación de un asiento junto con sus movimientos anidados.
    """
    movimientos = MovimientoContableSerializer(many=True)

    class Meta:
        model = AsientoContable
        fields = ['id', 'fecha', 'tercero', 'concepto', 'descripcion', 'movimientos']
        read_only_fields = ['id']

    def validate(self, data):
        """
        Valida la partida doble: la suma de débitos debe ser igual a la suma de créditos.
        """
        movimientos = data.get('movimientos', [])
        if not movimientos:
            raise serializers.ValidationError("Un asiento debe tener al menos un movimiento.")

        total_debitos = sum(m.get('debito', 0) for m in movimientos)
        total_creditos = sum(m.get('credito', 0) for m in movimientos)

        if total_debitos != total_creditos:
            raise serializers.ValidationError(f"Partida doble no cumplida. Débitos: {total_debitos}, Créditos: {total_creditos}")

        if total_debitos == 0:
            raise serializers.ValidationError("El total de débitos y créditos no puede ser cero.")

        return data

    def create(self, validated_data):
        """
        Crea el AsientoContable y sus MovimientoContable asociados en una transacción atómica.
        """
        movimientos_data = validated_data.pop('movimientos')

        with transaction.atomic():
            asiento = AsientoContable.objects.create(**validated_data)
            for movimiento_data in movimientos_data:
                MovimientoContable.objects.create(asiento=asiento, **movimiento_data)

        return asiento