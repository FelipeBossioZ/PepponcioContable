from rest_framework import serializers
from .models import Tercero

class TerceroSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Tercero.
    Permite la serialización y deserialización de los datos de Terceros.
    """
    nombre = serializers.CharField(source="nombre_razon_social", read_only=True)  # 👈 alias estable


    class Meta:
        model = Tercero
        fields = [
            'id',
            'tipo_documento',
            'numero_documento',
            'nombre_razon_social',
            'nombre',
            'direccion',
            'telefono',
            'email',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']