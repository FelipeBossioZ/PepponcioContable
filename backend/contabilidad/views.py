from rest_framework import viewsets, filters, views
from rest_framework.response import Response
from .models import Cuenta, AsientoContable, MovimientoContable
from .serializers import CuentaSerializer, AsientoContableSerializer, MovimientoContableSerializer

class CuentaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar las Cuentas Contables.

    Proporciona las acciones `list` y `retrieve` (solo lectura).
    Permite filtrar por el nombre de la cuenta.
    """
    queryset = Cuenta.objects.all()
    serializer_class = CuentaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['codigo', 'nombre']

class AsientoContableViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Asientos Contables.

    Permite crear, listar y ver el detalle de los asientos.
    La actualización y eliminación se deshabilitan por seguridad contable,
    ya que los asientos no deben modificarse (se deben crear asientos de ajuste).
    """
    queryset = AsientoContable.objects.prefetch_related('movimientos').all()
    serializer_class = AsientoContableSerializer
    http_method_names = ['get', 'post', 'head', 'options'] # Deshabilitar PUT, PATCH, DELETE

    def get_queryset(self):
        """
        Opcionalmente filtra los asientos por un rango de fechas.
        """
        queryset = super().get_queryset()
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')

        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)

        return queryset

class LibroDiarioView(views.APIView):
    """
    Vista para generar el reporte de Libro Diario.
    Devuelve todos los movimientos contables ordenados por fecha.
    """
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        movimientos = MovimientoContable.objects.select_related('asiento', 'cuenta').all().order_by('asiento__fecha', 'asiento__id')

        if fecha_inicio:
            movimientos = movimientos.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:
            movimientos = movimientos.filter(asiento__fecha__lte=fecha_fin)

        # Usamos un serializer simple para devolver solo los datos necesarios
        data = []
        for m in movimientos:
            data.append({
                'fecha': m.asiento.fecha,
                'asiento_id': m.asiento.id,
                'tercero': m.asiento.tercero.nombre_razon_social,
                'codigo_cuenta': m.cuenta.codigo,
                'nombre_cuenta': m.cuenta.nombre,
                'concepto': m.asiento.concepto,
                'debito': m.debito,
                'credito': m.credito
            })

        return Response(data)

class BalancePruebasView(views.APIView):
    """
    Vista para generar el reporte de Balance de Pruebas.
    Agrupa los movimientos por cuenta y calcula los saldos débito y crédito.
    """
    def get(self, request):
        from django.db.models import Sum

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        # Obtenemos todas las cuentas para asegurar que aparecen incluso si no tienen movimiento
        cuentas = Cuenta.objects.all().order_by('codigo')

        # Filtramos los movimientos por fecha
        movimientos = MovimientoContable.objects.all()
        if fecha_inicio:
            movimientos = movimientos.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:
            movimientos = movimientos.filter(asiento__fecha__lte=fecha_fin)

        # Agrupamos y sumamos
        saldos = movimientos.values('cuenta__codigo', 'cuenta__nombre') \
                            .annotate(total_debito=Sum('debito'), total_credito=Sum('credito')) \
                            .order_by('cuenta__codigo')

        # Creamos un diccionario para facilitar la búsqueda de saldos
        saldos_dict = {
            item['cuenta__codigo']: {
                'total_debito': item['total_debito'],
                'total_credito': item['total_credito']
            } for item in saldos
        }

        # Construimos la respuesta final
        reporte = []
        total_debitos_final = 0
        total_creditos_final = 0

        for cuenta in cuentas:
            saldo_info = saldos_dict.get(cuenta.codigo)
            if saldo_info:
                total_debito = saldo_info['total_debito']
                total_credito = saldo_info['total_credito']

                if total_debito > 0 or total_credito > 0:
                    reporte.append({
                        'codigo_cuenta': cuenta.codigo,
                        'nombre_cuenta': cuenta.nombre,
                        'total_debito': total_debito,
                        'total_credito': total_credito
                    })
                    total_debitos_final += total_debito
                    total_creditos_final += total_credito

        return Response({
            'detalle': reporte,
            'sumas_iguales': {
                'total_debitos': total_debitos_final,
                'total_creditos': total_creditos_final,
                'balance_correcto': total_debitos_final == total_creditos_final
            }
        })

class LibroMayorView(views.APIView):
    """
    Vista para generar el reporte de Libro Mayor para una cuenta específica.
    """
    def get(self, request, codigo_cuenta):
        from django.db.models import Sum, Q
        from decimal import Decimal

        try:
            cuenta = Cuenta.objects.get(pk=codigo_cuenta)
        except Cuenta.DoesNotExist:
            return Response({"error": "La cuenta especificada no existe."}, status=404)

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        # 1. Calcular Saldo Inicial
        saldo_inicial = Decimal('0.00')
        movimientos_anteriores = MovimientoContable.objects.filter(cuenta=cuenta)
        if fecha_inicio:
            # Para el saldo inicial, consideramos todos los movimientos ANTES de la fecha de inicio.
            movimientos_anteriores = movimientos_anteriores.filter(asiento__fecha__lt=fecha_inicio)
        else:
            # Si no hay fecha de inicio, no hay saldo inicial, empezamos desde cero.
            movimientos_anteriores = MovimientoContable.objects.none()

        saldo_anterior_agg = movimientos_anteriores.aggregate(
            total_debito=Sum('debito'),
            total_credito=Sum('credito')
        )
        debito_anterior = saldo_anterior_agg['total_debito'] or Decimal('0.00')
        credito_anterior = saldo_anterior_agg['total_credito'] or Decimal('0.00')
        saldo_inicial = debito_anterior - credito_anterior

        # 2. Obtener Movimientos del Período
        movimientos_periodo = MovimientoContable.objects.filter(cuenta=cuenta)
        if fecha_inicio:
            movimientos_periodo = movimientos_periodo.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:
            movimientos_periodo = movimientos_periodo.filter(asiento__fecha__lte=fecha_fin)

        movimientos_periodo = movimientos_periodo.select_related('asiento', 'asiento__tercero').order_by('asiento__fecha', 'asiento__id')

        # 3. Serializar y calcular saldo corriente
        detalle_movimientos = []
        saldo_corriente = saldo_inicial
        for m in movimientos_periodo:
            saldo_corriente += m.debito - m.credito
            detalle_movimientos.append({
                'fecha': m.asiento.fecha,
                'asiento_id': m.asiento.id,
                'tercero': m.asiento.tercero.nombre_razon_social,
                'concepto': m.asiento.concepto,
                'debito': m.debito,
                'credito': m.credito,
                'saldo': saldo_corriente
            })

        return Response({
            'cuenta': CuentaSerializer(cuenta).data,
            'fecha_inicio_reporte': fecha_inicio,
            'fecha_fin_reporte': fecha_fin,
            'saldo_inicial': saldo_inicial,
            'movimientos': detalle_movimientos,
            'saldo_final': saldo_corriente
        })

class EstadoResultadosView(views.APIView):
    """
    Vista para generar el Estado de Resultados a una fecha de corte.
    """
    def get(self, request):
        from django.db.models import Sum
        from decimal import Decimal

        fecha_fin = request.query_params.get('fecha_fin')
        if not fecha_fin:
            return Response({"error": "Debe proporcionar una 'fecha_fin' en los parámetros."}, status=400)

        # 1. Ingresos (Clase 4)
        ingresos_agg = MovimientoContable.objects.filter(
            asiento__fecha__lte=fecha_fin,
            cuenta__codigo__startswith='4'
        ).aggregate(total_credito=Sum('credito'), total_debito=Sum('debito'))
        total_ingresos = (ingresos_agg['total_credito'] or 0) - (ingresos_agg['total_debito'] or 0)

        # 2. Costos de Ventas (Clase 6)
        costos_agg = MovimientoContable.objects.filter(
            asiento__fecha__lte=fecha_fin,
            cuenta__codigo__startswith='6'
        ).aggregate(total_debito=Sum('debito'), total_credito=Sum('credito'))
        total_costos = (costos_agg['total_debito'] or 0) - (costos_agg['total_credito'] or 0)

        utilidad_bruta = total_ingresos - total_costos

        # 3. Gastos Operacionales (Clase 5)
        gastos_agg = MovimientoContable.objects.filter(
            asiento__fecha__lte=fecha_fin,
            cuenta__codigo__startswith='5'
        ).aggregate(total_debito=Sum('debito'), total_credito=Sum('credito'))
        total_gastos = (gastos_agg['total_debito'] or 0) - (gastos_agg['total_credito'] or 0)

        utilidad_operacional = utilidad_bruta - total_gastos

        # Por ahora, un cálculo simplificado. Se pueden añadir más niveles (no operacionales, impuestos, etc.)
        utilidad_neta_antes_impuestos = utilidad_operacional

        return Response({
            'fecha_corte': fecha_fin,
            'ingresos_operacionales': total_ingresos,
            'costo_de_ventas': total_costos,
            'utilidad_bruta': utilidad_bruta,
            'gastos_operacionales': total_gastos,
            'utilidad_operacional': utilidad_operacional,
            'utilidad_neta_antes_de_impuestos': utilidad_neta_antes_impuestos
        })

class BalanceGeneralView(views.APIView):
    """
    Vista para generar el Balance General (Estado de Situación Financiera).
    """
    def get(self, request):
        from django.db.models import Sum
        from decimal import Decimal

        fecha_fin = request.query_params.get('fecha_fin')
        if not fecha_fin:
            return Response({"error": "Debe proporcionar una 'fecha_fin' en los parámetros."}, status=400)

        # Función auxiliar para calcular el saldo de una clase de cuenta
        def calcular_saldo_clase(clase):
            movimientos = MovimientoContable.objects.filter(
                asiento__fecha__lte=fecha_fin,
                cuenta__codigo__startswith=str(clase)
            )
            saldo = movimientos.aggregate(
                total_debito=Sum('debito', default=Decimal(0)),
                total_credito=Sum('credito', default=Decimal(0))
            )
            return saldo['total_debito'] - saldo['total_credito']

        # Calcular saldos para Activo (1), Pasivo (2), y Patrimonio (3)
        total_activos = calcular_saldo_clase(1)
        total_pasivos = calcular_saldo_clase(2) * -1 # Se multiplica por -1 porque los pasivos son de naturaleza crédito
        total_patrimonio_inicial = calcular_saldo_clase(3) * -1

        # Calcular la utilidad del ejercicio (Ingresos - Gastos - Costos)
        utilidad_ingresos = calcular_saldo_clase(4) * -1
        utilidad_gastos = calcular_saldo_clase(5)
        utilidad_costos = calcular_saldo_clase(6)
        utilidad_del_ejercicio = utilidad_ingresos - utilidad_gastos - utilidad_costos

        total_patrimonio = total_patrimonio_inicial + utilidad_del_ejercicio

        # Verificación de la ecuación contable
        ecuacion_ok = total_activos == (total_pasivos + total_patrimonio)

        return Response({
            'fecha_corte': fecha_fin,
            'activos': {
                'total': total_activos,
            },
            'pasivos_y_patrimonio': {
                'total_pasivos': total_pasivos,
                'total_patrimonio': total_patrimonio,
                'total_pasivo_y_patrimonio': total_pasivos + total_patrimonio,
            },
            'verificacion_ecuacion_contable': {
                'ecuacion': 'Activo = Pasivo + Patrimonio',
                'balance_correcto': ecuacion_ok
            }
        })

class MediosMagneticosView(views.APIView):
    """
    Vista para generar reportes de Medios Magnéticos (Exógena) para la DIAN.
    """
    def get(self, request, formato):
        year = request.query_params.get('year')
        if not year:
            return Response({"error": "Debe proporcionar el parámetro 'year'."}, status=400)

        if formato == '1001':
            return self.formato_1001(year)

        # Aquí se añadirían las llamadas a otros formatos (1003, 1005, etc.)

        return Response({"error": f"El formato '{formato}' no es soportado aún."}, status=404)

    def formato_1001(self, year):
        """
        Genera los datos para el Formato 1001 v10: Pagos o abonos en cuenta.
        Conceptos de ejemplo: 5002 (Salarios), 5016 (Honorarios).
        """
        from django.db.models import Sum, Value, CharField
        from django.db.models.functions import Coalesce

        # Filtra movimientos de cuentas de Gasto (clase 5) para el año especificado.
        pagos = MovimientoContable.objects.filter(
            asiento__fecha__year=year,
            cuenta__codigo__startswith='5'
        ).values(
            'asiento__tercero__tipo_documento',
            'asiento__tercero__numero_documento',
            'asiento__tercero__nombre_razon_social'
        ).annotate(
            # Agregamos el concepto basado en la cuenta. Lógica de ejemplo.
            concepto_pago=Value('5016', output_field=CharField()), # Asumimos honorarios por defecto
            valor_pago=Sum('debito')
        ).filter(valor_pago__gt=0) # Solo pagos, no notas crédito

        # Aquí iría una lógica más compleja para mapear cuentas a conceptos DIAN.
        # Por ahora, es una implementación de ejemplo.

        data = list(pagos)

        return Response({
            'formato': '1001',
            'version': '10',
            'año': year,
            'registros': data
        })