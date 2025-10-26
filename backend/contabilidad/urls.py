
 #contabilidad/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CuentaViewSet,
    AsientoContableViewSet,
    LibroDiarioView,
    BalancePruebasView,
    LibroMayorView,
    EstadoResultadosView,
    BalanceGeneralView,
    MediosMagneticosView,
    PeriodoView, AuxiliarPorTerceroView
)



# Creamos un router para registrar las vistas de la API
router = DefaultRouter()
router.register(r'cuentas', CuentaViewSet, basename='cuenta')
router.register(r'asientos', AsientoContableViewSet, basename='asiento')

# Las URLs de la API son determinadas automáticamente por el router.
# Añadimos las URLs para los reportes manualmente.
urlpatterns = [
    path('', include(router.urls)),
    path('reportes/libro-diario/', LibroDiarioView.as_view(), name='libro-diario'),
    path('reportes/balance-pruebas/', BalancePruebasView.as_view(), name='balance-pruebas'),
    path('reportes/libro-mayor/<str:codigo_cuenta>/', LibroMayorView.as_view(), name='libro-mayor'),
    path('reportes/estado-resultados/', EstadoResultadosView.as_view(), name='estado-resultados'),
    path('reportes/balance-general/', BalanceGeneralView.as_view(), name='balance-general'),
    path('reportes/medios-magneticos/<str:formato>/', MediosMagneticosView.as_view(), name='medios-magneticos'),
    path('periodo/', PeriodoView.as_view(), name='periodo'),
    path('reportes/auxiliar-tercero/', AuxiliarPorTerceroView.as_view(), name='auxiliar-tercero'),
]