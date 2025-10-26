from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacturaViewSet
from .views import FacturaPDFView

router = DefaultRouter()
router.register(r'facturas', FacturaViewSet, basename='factura')

urlpatterns = [
    path('', include(router.urls)),
    path('facturas/<int:pk>/pdf/', FacturaPDFView.as_view(), name='factura-pdf'),
]