from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

schema_view = get_schema_view(
   openapi.Info(
      title="PYME Contable API",
      default_version='v1',
      description="Documentación de la API para el sistema contable.",
      contact=openapi.Contact(email="contacto@tuproyecto.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# backend/pyme_contable_backend/urls.py (Sección urlpatterns)

# ... (Las importaciones son correctas) ...

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. API REST con prefijos únicos y descriptivos
    # Note: Aquí se le da el prefijo base a la aplicación de Django
    path('api/terceros/', include('terceros.urls')),     
    path('api/contabilidad/', include('contabilidad.urls')), 
    path('api/facturacion/', include('facturacion.urls')),   
    
    # 2. Endpoints de autenticación por Token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. Endpoints de Documentación de la API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]