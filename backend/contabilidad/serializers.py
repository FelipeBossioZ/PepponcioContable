# backend/contabilidad/serializers.py
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Cuenta, AsientoContable, MovimientoContable
# Si tu Asiento tiene FK a Tercero, descomenta:
# from terceros.models import Tercero

# --- Plan de cuentas ---
class CuentaSerializer(serializers.ModelSerializer):
    padre = serializers.SlugRelatedField(slug_field="codigo", read_only=True)

    class Meta:
        model = Cuenta
        fields = ["codigo", "nombre", "padre"]  # 👈 nada de 'id'


# --- Movimientos ---
class MovimientoContableSerializer(serializers.ModelSerializer):
    # Permite mandar código en lugar de ID de cuenta
    cuenta_codigo = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = MovimientoContable
        fields = ["id", "cuenta", "cuenta_codigo", "debito", "credito"]
        extra_kwargs = {
            "cuenta": {"required": False},  # porque podemos usar cuenta_codigo
        }

    def validate(self, attrs):
        if not attrs.get("cuenta") and not attrs.get("cuenta_codigo"):
            raise serializers.ValidationError("Debe enviar 'cuenta' (id) o 'cuenta_codigo' (código).")
        return attrs

    def _resolve_cuenta(self, attrs):
        code = attrs.pop("cuenta_codigo", None)
        if code and not attrs.get("cuenta"):
            try:
                attrs["cuenta"] = Cuenta.objects.get(codigo=code)
            except Cuenta.DoesNotExist:
                raise serializers.ValidationError({"cuenta_codigo": f"No existe la cuenta con código '{code}'."})
        return attrs

    def create(self, validated_data):
        validated_data = self._resolve_cuenta(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._resolve_cuenta(validated_data)
        return super().update(instance, validated_data)


# --- Asiento con movimientos anidados ---
class AsientoContableSerializer(serializers.ModelSerializer):
    movimientos = MovimientoContableSerializer(many=True)
    # Si usas tercero en el modelo:
    # tercero = serializers.PrimaryKeyRelatedField(queryset=Tercero.objects.all(), required=False, allow_null=True)

    class Meta:
        model = AsientoContable
        fields = [
            "id","fecha","concepto","tercero","descripcion_adicional",
            "movimientos","estado","anulado_por","anulado_en","anulacion_motivo","ajusta_a"
        ]
        read_only_fields = ["id","estado","anulado_por","anulado_en","ajusta_a"]

    def validate(self, attrs):
        movs = attrs.get("movimientos", [])
        total_deb = sum(Decimal(str(m.get("debito", 0))) for m in movs)
        total_cred = sum(Decimal(str(m.get("credito", 0))) for m in movs)
        if total_deb != total_cred:
            raise serializers.ValidationError("Los débitos y créditos deben ser iguales.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        movimientos_data = validated_data.pop("movimientos", [])
        asiento = AsientoContable.objects.create(**validated_data)
        for m in movimientos_data:
            m["asiento"] = asiento
            MovimientoContableSerializer().create(m)
        return asiento

    # (opcional) update anidado, si algún día lo necesitas:
    # @transaction.atomic
    # def update(self, instance, validated_data):
    #     movimientos_data = validated_data.pop("movimientos", None)
    #     for attr, val in validated_data.items():
    #         setattr(instance, attr, val)
    #     instance.save()
    #     if movimientos_data is not None:
    #         instance.movimientos.all().delete()
    #         for m in movimientos_data:
    #             m["asiento"] = instance
    #             MovimientoContableSerializer().create(m)
    #     return instance
