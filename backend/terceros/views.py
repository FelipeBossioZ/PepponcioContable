from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny   # 👈 añade esto
from .models import Tercero
from .serializers import TerceroSerializer

class TerceroViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión completa (CRUD) de Terceros.
    """
    permission_classes = [AllowAny]   # DEV

    queryset = Tercero.objects.all().order_by('nombre_razon_social')
    serializer_class = TerceroSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['numero_documento', 'nombre_razon_social']