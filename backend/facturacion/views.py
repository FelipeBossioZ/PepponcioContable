from rest_framework import viewsets, filters
from .models import Factura
from .serializers import FacturaSerializer

class FacturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Facturas (CRUD).
    Permite crear, leer, actualizar y eliminar facturas.
    """
    queryset = Factura.objects.prefetch_related('items').all()
    serializer_class = FacturaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['cliente__nombre_razon_social', 'cliente__numero_documento', 'id']