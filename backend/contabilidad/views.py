#contabilidad/views.py

from rest_framework import viewsets, filters, views
from rest_framework.response import Response
#from rest_framework.permissions import AllowAny   # 👈 añade esto
from .models import Cuenta, AsientoContable, MovimientoContable
from .serializers import CuentaSerializer, AsientoContableSerializer, MovimientoContableSerializer
from django.utils import timezone
from datetime import date
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import PeriodoContable
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font
from django.http import HttpResponse
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime
from rest_framework.permissions import IsAdminUser
from .serializers import PeriodoContableSerializer



def _parse_date(val):
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):  # ISO y día/mes/año
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None

class PeriodoView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        anio = request.query_params.get("anio")
        if not anio:
            anio = timezone.localdate().year
        else:
            anio = int(anio)
        obj, _ = PeriodoContable.objects.get_or_create(anio=anio, defaults={"estado":"abierto"})
        return Response(PeriodoContableSerializer(obj).data)

    def patch(self, request):
        # sólo admin puede editar
        self.permission_classes = [IsAdminUser]
        anio = int(request.data.get("anio"))
        try:
            obj = PeriodoContable.objects.get(anio=anio)
        except PeriodoContable.DoesNotExist:
            return Response({"detail": "Periodo no existe."}, status=404)
        ser = PeriodoContableSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save(cerrado_por=request.user if ser.validated_data.get("estado") == "cerrado" else obj.cerrado_por)
        return Response(ser.data)

class AuxiliarPorTerceroView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tercero_id  = request.query_params.get('tercero_id')
        fecha_inicio= request.query_params.get('fecha_inicio')
        fecha_fin   = request.query_params.get('fecha_fin')
        formato     = request.query_params.get('formato')

        if not tercero_id:
            return Response({"error":"tercero_id requerido"}, status=400)

        qs = (MovimientoContable.objects
              .select_related("asiento","cuenta","asiento__tercero")
              .filter(asiento__tercero_id=tercero_id))
        if fecha_inicio: qs = qs.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:    qs = qs.filter(asiento__fecha__lte=fecha_fin)
        qs = qs.order_by('asiento__fecha','asiento_id','id')

        # saldo inicial (antes del rango)
        prev = MovimientoContable.objects.filter(asiento__tercero_id=tercero_id)
        if fecha_inicio: prev = prev.filter(asiento__fecha__lt=fecha_inicio)
        agg = prev.aggregate(d=Sum("debito"), c=Sum("credito"))
        saldo = (agg["d"] or 0) - (agg["c"] or 0)

        if formato == "xlsx":
            wb = Workbook(); ws = wb.active; ws.title="Auxiliar por tercero"
            ws.append(["Auxiliar por tercero", f"ID {tercero_id}"])
            ws.append([f"Rango: {fecha_inicio or '----'} a {fecha_fin or '----'}"])
            ws.append([])
            ws.append(["Saldo inicial", float(saldo)])
            ws.append([])
            ws.append(["Fecha","Asiento #","Cuenta","Nombre","Concepto","Débito","Crédito","Saldo"])
            for cell in ws[6]: cell.font = Font(bold=True)

            for m in qs:
                saldo += m.debito - m.credito
                ws.append([
                    m.asiento.fecha.isoformat(), m.asiento.id, m.cuenta.codigo, m.cuenta.nombre,
                    m.asiento.concepto, float(m.debito), float(m.credito), float(saldo)
                ])

            for col, w in enumerate([12,12,12,32,36,14,14,14], start=1):
                ws.column_dimensions[get_column_letter(col)].width = w
            ws.freeze_panes = "A7"

            resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = 'attachment; filename="auxiliar_tercero.xlsx"'
            wb.save(resp); return resp

        # JSON simple
        data = []
        for m in qs:
            saldo += m.debito - m.credito
            data.append({
                "fecha": m.asiento.fecha, "asiento_id": m.asiento.id,
                "cuenta": m.cuenta.codigo, "nombre_cuenta": m.cuenta.nombre,
                "concepto": m.asiento.concepto, "debito": m.debito,
                "credito": m.credito, "saldo": saldo
            })
        return Response({"saldo_inicial":saldo, "movimientos":data})




class CuentaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar las Cuentas Contables.

    Proporciona las acciones `list` y `retrieve` (solo lectura).
    Permite filtrar por el nombre de la cuenta.
    """
    
    queryset = Cuenta.objects.all().order_by("codigo")
    serializer_class = CuentaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["codigo", "nombre"]
    pagination_class = None

class AsientoContableViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Asientos Contables.

    Permite crear, listar y ver el detalle de los asientos.
    La actualización y eliminación se deshabilitan por seguridad contable,
    ya que los asientos no deben modificarse (se deben crear asientos de ajuste).
    """
    permission_classes = [IsAuthenticated]
    
    queryset = AsientoContable.objects.prefetch_related("movimientos").all()
    serializer_class = AsientoContableSerializer
    http_method_names = ['get', 'post', 'head', 'options'] # Deshabilitar PUT, PATCH, DELETE

    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request, pk=None):
        asiento = self.get_object()
        if asiento.estado == "anulado":
            return Response({"detail": "El asiento ya está anulado."}, status=400)

        hoy = timezone.localdate()
        periodo = PeriodoContable.periodo_para_fecha(asiento.fecha)  # periodo del año del asiento

        # Reglas:
        #  - Si el periodo del asiento está "cerrado": prohibido.
        #  - Si está "abierto" y hoy <= 31/12 del mismo año: anula sin PIN.
        #  - Si hoy es 01/01–31/03 del año siguiente y 'ventana_enero_marzo' = True: requiere PINs.
        #  - Fuera de esas ventanas: prohibido.
        if periodo.estado == "cerrado":
            return Response({"detail": f"El periodo {periodo.anio} está CERRADO. Anulación prohibida."}, status=403)

        limite_libre = date(asiento.fecha.year, 12, 31)
        limite_pin   = date(asiento.fecha.year + 1, 3, 31)

        requiere_pins = False
        if hoy <= limite_libre:
            requiere_pins = False
        elif hoy <= limite_pin and periodo.ventana_enero_marzo:
            requiere_pins = True
        else:
            return Response({"detail": "Fuera de la ventana permitida para anulación."}, status=403)

        if requiere_pins:
            from django.conf import settings
            contador_pin = request.data.get("contador_pin")
            gerente_pin  = request.data.get("gerente_pin")
            ok_cont = bool(contador_pin) and (contador_pin == getattr(settings, "CONTADOR_PIN", None))
            ok_ger  = bool(gerente_pin)  and (gerente_pin  == getattr(settings, "GERENTE_PIN", None))
            if not (ok_cont and ok_ger):
                return Response({"detail": "Se requieren PINs válidos de Contador y Gerente."}, status=403)

        motivo = request.data.get("motivo", "")

        # Crear asiento de ajuste (inverso) y marcar anulado
        ajuste = AsientoContable.objects.create(
            fecha = hoy,
            concepto = f"AJUSTE POR ANULACIÓN del asiento #{asiento.id}",
            tercero = asiento.tercero,
            descripcion_adicional = f"Motivo: {motivo}",
        )
        for m in asiento.movimientos.all():
            MovimientoContable.objects.create(
                asiento = ajuste,
                cuenta = m.cuenta,
                debito = m.credito,
                credito = m.debito,
            )

        asiento.estado = "anulado"
        asiento.anulado_por = request.user
        asiento.anulado_en = timezone.now()
        asiento.anulacion_motivo = motivo
        asiento.ajusta_a = ajuste
        asiento.save()

        return Response({"detail": "Asiento anulado y ajuste generado", "ajuste_id": ajuste.id}, status=200)

    def get_queryset(self):
        """
        Opcionalmente filtra los asientos por un rango de fechas.
        """
        qs = super().get_queryset()
        fi = _parse_date(self.request.query_params.get('fecha_inicio'))
        ff = _parse_date(self.request.query_params.get('fecha_fin'))
        if fi:
            qs = qs.filter(fecha__gte=fi)
        if ff:
            qs = qs.filter(fecha__lte=ff)
        return qs

class LibroDiarioView(views.APIView):
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin    = request.query_params.get('fecha_fin')
        formato      = request.query_params.get('formato')

        qs = (MovimientoContable.objects
              .select_related('asiento', 'cuenta', 'asiento__tercero')
              .order_by('asiento__fecha', 'asiento__id', 'id'))
        if fecha_inicio: qs = qs.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:    qs = qs.filter(asiento__fecha__lte=fecha_fin)

        if formato == "xlsx":
            wb = Workbook(); ws = wb.active; ws.title = "Libro Diario"
            ws.append(["Fecha","Asiento #","Tercero","Cuenta","Nombre cuenta","Concepto","Débito","Crédito"])
            for cell in ws[1]: cell.font = Font(bold=True)
            for m in qs:
                ws.append([
                    m.asiento.fecha.isoformat(),
                    m.asiento.id,
                    getattr(m.asiento.tercero, 'nombre_razon_social', "") or "",
                    m.cuenta.codigo, m.cuenta.nombre,
                    m.asiento.concepto,
                    float(m.debito), float(m.credito),
                ])
            for col, w in enumerate([12,12,30,12,32,36,14,14], start=1):
                ws.column_dimensions[get_column_letter(col)].width = w
            ws.freeze_panes = "A2"
            resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = 'attachment; filename="libro_diario.xlsx"'
            wb.save(resp); return resp

        # JSON (ligero)
        data = [{
            'fecha': m.asiento.fecha,
            'asiento_id': m.asiento.id,
            'tercero': getattr(m.asiento.tercero, 'nombre_razon_social', None),
            'codigo_cuenta': m.cuenta.codigo,
            'nombre_cuenta': m.cuenta.nombre,
            'concepto': m.asiento.concepto,
            'debito': m.debito, 'credito': m.credito
        } for m in qs]
        return Response(data)



class BalancePruebasView(views.APIView):
    def get(self, request):
        from collections import defaultdict

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin    = request.query_params.get('fecha_fin')
        formato      = request.query_params.get('formato')

        cuentas = Cuenta.objects.all().order_by('codigo')

        movs = MovimientoContable.objects.all()
        if fecha_inicio: movs = movs.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:    movs = movs.filter(asiento__fecha__lte=fecha_fin)

        # Saldo inicial (antes del rango)
        prev = MovimientoContable.objects.all()
        if fecha_inicio: prev = prev.filter(asiento__fecha__lt=fecha_inicio)

        saldo_inicial = defaultdict(lambda: Decimal('0'))
        for p in prev.values('cuenta__codigo').annotate(d=Sum('debito'), c=Sum('credito')):
            codigo = p['cuenta__codigo']
            d = p['d'] or 0; c = p['c'] or 0
            saldo_inicial[codigo] = Decimal(d) - Decimal(c)

        # Débitos/Créditos del período
        period = {}
        for s in (movs.values('cuenta__codigo', 'cuenta__nombre')
                       .annotate(total_debito=Sum('debito'), total_credito=Sum('credito'))
                       .order_by('cuenta__codigo')):
            codigo = s['cuenta__codigo']
            period[codigo] = {
                'nombre': s['cuenta__nombre'],
                'deb': Decimal(s['total_debito'] or 0),
                'cre': Decimal(s['total_credito'] or 0)
            }

        reporte = []
        tot_deb = Decimal('0'); tot_cre = Decimal('0')
        for cta in cuentas:
            cod = cta.codigo
            ini = saldo_inicial[cod]
            deb = period.get(cod, {}).get('deb', Decimal('0'))
            cre = period.get(cod, {}).get('cre', Decimal('0'))
            fin = ini + deb - cre
            # Mostrar filas con movimiento o con saldos:
            if ini != 0 or deb != 0 or cre != 0 or fin != 0:
                reporte.append({
                    'codigo_cuenta': cod,
                    'nombre_cuenta': cta.nombre,
                    'saldo_inicial': ini,
                    'total_debito':  deb,
                    'total_credito': cre,
                    'saldo_final':   fin,
                })
                tot_deb += deb; tot_cre += cre

        if formato == "xlsx":
            wb = Workbook(); ws = wb.active; ws.title = "Balance de Prueba"
            ws.append(["Empresa / NIT"]) ; ws.append([f"Balance de Prueba  {fecha_inicio or ''} a {fecha_fin or ''}"])
            for i in (1,2): ws[f"A{i}"].font = Font(bold=True)
            ws.append([])
            ws.append(["Cuenta","Nombre","Saldo inicial","Débitos","Créditos","Saldo final"])
            for cell in ws[4]: cell.font = Font(bold=True)

            for row in reporte:
                ws.append([
                    row["codigo_cuenta"], row["nombre_cuenta"],
                    float(row["saldo_inicial"]), float(row["total_debito"]),
                    float(row["total_credito"]), float(row["saldo_final"])
                ])
            ws.append([])
            ws.append(["", "TOTALES", "", float(tot_deb), float(tot_cre), ""])

            for col, w in enumerate([12,36,16,14,14,16], start=1):
                ws.column_dimensions[get_column_letter(col)].width = w
            ws.freeze_panes = "A5"

            resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = 'attachment; filename="balance_prueba.xlsx"'
            wb.save(resp); return resp

        return Response({
            'detalle': reporte,
            'sumas_iguales': {
                'total_debitos':  tot_deb,
                'total_creditos': tot_cre,
                'balance_correcto': tot_deb == tot_cre
            }
        }, status=200)



class LibroMayorView(views.APIView):
    def get(self, request, codigo_cuenta):
        try:
            cuenta = Cuenta.objects.get(pk=codigo_cuenta)
        except Cuenta.DoesNotExist:
            return Response({"error": "La cuenta especificada no existe."}, status=404)

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin    = request.query_params.get('fecha_fin')
        formato      = request.query_params.get('formato')

        # saldo inicial (antes de fecha_inicio)
        prev = MovimientoContable.objects.filter(cuenta=cuenta)
        if fecha_inicio: prev = prev.filter(asiento__fecha__lt=fecha_inicio)
        agg_prev = prev.aggregate(total_debito=Sum('debito'), total_credito=Sum('credito'))
        deb_prev = agg_prev['total_debito']  or Decimal('0')
        cre_prev = agg_prev['total_credito'] or Decimal('0')
        saldo_inicial = deb_prev - cre_prev

        # movimientos del período
        qs = MovimientoContable.objects.filter(cuenta=cuenta)
        if fecha_inicio: qs = qs.filter(asiento__fecha__gte=fecha_inicio)
        if fecha_fin:    qs = qs.filter(asiento__fecha__lte=fecha_fin)
        qs = qs.select_related('asiento','asiento__tercero').order_by('asiento__fecha','asiento__id','id')

        saldo = saldo_inicial
        detalle = []
        for m in qs:
            saldo += m.debito - m.credito
            detalle.append({
                'fecha': m.asiento.fecha,
                'asiento_id': m.asiento.id,
                'tercero': getattr(m.asiento.tercero, 'nombre_razon_social', None),
                'concepto': m.asiento.concepto,
                'debito': m.debito, 'credito': m.credito,
                'saldo': saldo,
            })

        if formato == "xlsx":
            wb = Workbook(); ws = wb.active; ws.title = f"Mayor {cuenta.codigo}"
            ws.append([f"Libro Mayor — {cuenta.codigo} {cuenta.nombre}"])
            ws.append([f"Rango: {fecha_inicio or '----'} a {fecha_fin or '----'}"])
            ws.append([])

            ws.append(["Saldo inicial", float(saldo_inicial)])
            ws.append([])
            ws.append(["Fecha","Asiento #","Tercero","Concepto","Débito","Crédito","Saldo"])
            for cell in ws[6]: cell.font = Font(bold=True)

            for row in detalle:
                ws.append([
                    row["fecha"].isoformat(), row["asiento_id"], row["tercero"] or "",
                    row["concepto"], float(row["debito"]), float(row["credito"]), float(row["saldo"])
                ])

            ws.append([])
            ws.append(["Saldo final", float(saldo)])
            for col, w in enumerate([12,12,30,36,14,14,14], start=1):
                ws.column_dimensions[get_column_letter(col)].width = w
            ws.freeze_panes = "A7"
            resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = f'attachment; filename="libro_mayor_{cuenta.codigo}.xlsx"'
            wb.save(resp); return resp

        return Response({
            'cuenta': {'codigo': cuenta.codigo, 'nombre': cuenta.nombre},
            'fecha_inicio_reporte': fecha_inicio,
            'fecha_fin_reporte': fecha_fin,
            'saldo_inicial': saldo_inicial,
            'movimientos': detalle,
            'saldo_final': saldo,
        }, status=200)



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

        
