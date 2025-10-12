' ==================================================
' SISTEMA POS COMPLETO
'
' OPTIMIZADO POR JULES
' Versión 6.0 (Final, Completa y Verificada)
' ==================================================

' --- Declaraciones de API ---
Private Declare PtrSafe Function GetAsyncKeyState Lib "user32" (ByVal vKey As Long) As Integer

' ==================================================
' VARIABLES GLOBALES DEL FORMULARIO
' ==================================================

Private wsProductos As Worksheet, wsVentas As Worksheet, wsClientes As Worksheet
Private wsProveedores As Worksheet, wsRegistroPDF As Worksheet
Private ProductosEnMemoria As Object ' Scripting.Dictionary
Private numeroVenta As Long, filaProductoActual As Long
Private ModoInventario As Boolean

' ==================================================
' FUNCIONES DE FORMATO Y UTILIDADES
' ==================================================

Private Function FormatearPrecio(ByVal valor As Variant) As String
    If IsNumeric(valor) Then FormatearPrecio = Format(CDbl(valor), "$#,##0") Else FormatearPrecio = "$0"
End Function

Private Function LimpiarTextoPrecio(ByVal texto As String) As Double
    On Error Resume Next
    LimpiarTextoPrecio = CDbl(Replace(Replace(texto, "$", ""), ".", ""))
End Function

' ==================================================
' EVENTOS PRINCIPALES DEL FORMULARIO
' ==================================================

Private Sub UserForm_Initialize()
    On Error GoTo ErrorHandler
    Application.ScreenUpdating = False

    Me.Caption = "SISTEMA DE PUNTO DE VENTA (POS) - OPTIMIZADO"
    Me.Width = Application.Width * 0.9: Me.Height = Application.Height * 0.95
    Me.StartUpPosition = 0: Me.Top = Application.Top + (Application.Height - Me.Height) / 2: Me.Left = Application.Left + (Application.Width - Me.Width) / 2

    Set wsProductos = ThisWorkbook.Sheets("Hoja1"): Set wsVentas = ThisWorkbook.Sheets("Ventas"): Set wsClientes = ThisWorkbook.Sheets("Clientes")
    On Error Resume Next
    Set wsProveedores = ThisWorkbook.Sheets("Proveedores"): Set wsRegistroPDF = ThisWorkbook.Sheets("RegistroPDF")
    On Error GoTo 0

    Set ProductosEnMemoria = CreateObject("Scripting.Dictionary")
    Call CargarProductosEnMemoria
    Call DeterminarNumeroSiguienteVenta
    ModoInventario = False

    Call CargarClientesComboBox
    Call LimpiarVentaActual
    Call ConfigurarVisibilidadSegunPermisos
    Call AplicarTemaVisualModerno
    Call ConfigurarIconosEnBotones

    Me.MultiPage1.Value = 0
    Me.txtBuscar.SetFocus
    Call ActualizarResumenVentasDelDia

    Application.ScreenUpdating = True
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "Error Crítico al Inicializar: " & Err.Description, vbCritical, "Error de Inicialización"
    Unload Me
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If GetAsyncKeyState(vbKeyShift) < 0 Then Exit Sub
    If MsgBox("¿Desea cerrar el Sistema POS?" & vbCrLf & "Se creará un backup antes de salir.", vbYesNo + vbQuestion, "Confirmar Cierre") = vbNo Then
        Cancel = True: Exit Sub
    End If
    Call CrearBackupAlCerrar
    ThisWorkbook.Save
End Sub

' ==================================================
' NAVEGACIÓN Y MANEJO DE PESTAÑAS (MULTIPAGE)
' ==================================================

Private Sub MultiPage1_Change()
    Select Case Me.MultiPage1.Value
        Case 0: Me.Caption = "SISTEMA POS - MODO VENTA": Call ActualizarResumenVentasDelDia: Me.txtBuscar.SetFocus
        Case 1: Me.Caption = "SISTEMA POS - HISTORIAL DE VENTAS": Call CargarHistorialVentas
        Case 2: Me.Caption = "SISTEMA POS - REPORTES Y ESTADÍSTICAS": Call ActualizarDatosReportes
        Case 3: Me.Caption = "SISTEMA POS - AJUSTES DE INVENTARIO": Me.txtBuscarAjuste.SetFocus
    End Select
End Sub

' ==================================================
' PESTAÑA 0: VENTA (POS)
' ==================================================

Private Sub txtBuscar_KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)
    If KeyAscii = 13 Then Call BuscarProductosEnMemoria: KeyAscii = 0
End Sub

Private Sub btnBuscar_Click()
    Call BuscarProductosEnMemoria
End Sub

Private Sub lstProductos_DblClick(ByVal Cancel As MSForms.ReturnBoolean)
    If Me.lstProductos.ListIndex >= 0 Then Call AgregarProductoAVenta
End Sub

Private Sub btnAgregar_Click()
    Call AgregarProductoAVenta
End Sub

Private Sub btnEliminar_Click()
    Call EliminarProductoDeVenta
End Sub

Private Sub btnLimpiar_Click()
    Call LimpiarVentaActual
End Sub

Private Sub btnFinalizar_Click()
    Call FinalizarVenta
End Sub

Private Sub BuscarProductosEnMemoria()
    On Error GoTo ErrorHandler
    Dim textoBusqueda As String: textoBusqueda = UCase(Trim(Me.txtBuscar.Text))

    Me.lstProductos.Clear
    Me.txtValorUnd.Text = ""

    If textoBusqueda = "" Then Exit Sub

    Dim resultados() As Variant
    Dim encontrados As Long: encontrados = 0
    Dim key As Variant, producto As Variant

    For Each key In ProductosEnMemoria.Keys
        producto = ProductosEnMemoria(key)
        If InStr(1, UCase(key), textoBusqueda) > 0 Or InStr(1, UCase(producto(0)), textoBusqueda) > 0 Then
            encontrados = encontrados + 1
            ReDim Preserve resultados(1 To 4, 1 To encontrados)
            resultados(1, encontrados) = key
            resultados(2, encontrados) = producto(0)
            resultados(3, encontrados) = FormatearPrecio(producto(1))
            resultados(4, encontrados) = IIf(producto(2) > 0, producto(2), "SIN STOCK")
        End If
    Next key

    If encontrados > 0 Then
        Me.lstProductos.Column = resultados
        Me.lstProductos.ListIndex = 0
        Call lstProductos_Click
    Else
        Me.lstProductos.AddItem
        Me.lstProductos.List(0, 1) = "No se encontraron productos"
    End If
    Exit Sub
ErrorHandler:
    MsgBox "Error buscando productos: " & Err.Description, vbCritical
End Sub

Private Sub lstProductos_Click()
    On Error Resume Next
    If Me.lstProductos.ListIndex >= 0 Then
        Me.txtValorUnd.Text = Me.lstProductos.List(Me.lstProductos.ListIndex, 2)
    End If
End Sub

Private Sub AgregarProductoAVenta()
    On Error GoTo ErrorHandler
    If Me.lstProductos.ListIndex = -1 Or Me.lstProductos.List(Me.lstProductos.ListIndex, 0) = "" Then
        MsgBox "Seleccione un producto válido.", vbExclamation
        Exit Sub
    End If

    Dim cantidad As Long: cantidad = Val(Me.txtCantidad.Text)
    If cantidad <= 0 Then
        MsgBox "Cantidad inválida.", vbExclamation: Me.txtCantidad.SetFocus: Exit Sub
    End If

    Dim codigo As String: codigo = Me.lstProductos.List(Me.lstProductos.ListIndex, 0)
    If Not ProductosEnMemoria.Exists(codigo) Then
        MsgBox "Error: Producto no encontrado en la base de datos.", vbCritical: Exit Sub
    End If

    Dim producto As Variant: producto = ProductosEnMemoria(codigo)
    Dim descripcion As String: descripcion = producto(0)
    Dim precio As Double: precio = producto(1)
    Dim existencia As Long: existencia = producto(2)

    If existencia <= 0 Then
        If MsgBox("PRODUCTO SIN STOCK. ¿Vender de todos modos?", vbYesNo + vbExclamation, "Sin Stock") = vbNo Then Exit Sub
    ElseIf cantidad > existencia Then
        MsgBox "Stock insuficiente. Disponible: " & existencia, vbExclamation: Exit Sub
    End If

    Dim i As Long
    For i = 0 To Me.lstVenta.ListCount - 1
        If Me.lstVenta.List(i, 0) = codigo Then
            Dim nuevaCantidad As Long: nuevaCantidad = Val(Me.lstVenta.List(i, 2)) + cantidad
            Me.lstVenta.List(i, 2) = nuevaCantidad
            Me.lstVenta.List(i, 3) = FormatearPrecio(precio * nuevaCantidad)
            Call CalcularTotalVenta
            Me.txtCantidad.Text = "1": Me.txtBuscar.SetFocus: Exit Sub
        End If
    Next i

    Dim item(0 To 3) As String
    item(0) = codigo
    item(1) = descripcion & IIf(existencia <= 0, " [SIN STOCK]", "")
    item(2) = cantidad
    item(3) = FormatearPrecio(precio * cantidad)
    Me.lstVenta.AddItem Join(item, ";")

    Call CalcularTotalVenta
    Me.txtCantidad.Text = "1": Me.txtBuscar.Text = "": Me.txtBuscar.SetFocus
    Exit Sub
ErrorHandler:
    MsgBox "Error agregando producto: " & Err.Description, vbCritical
End Sub

Private Sub EliminarProductoDeVenta()
    If Me.lstVenta.ListIndex = -1 Then
        MsgBox "Seleccione un producto a eliminar.", vbExclamation: Exit Sub
    End If
    Me.lstVenta.RemoveItem Me.lstVenta.ListIndex
    Call CalcularTotalVenta
End Sub

Private Sub FinalizarVenta()
    On Error GoTo ErrorHandler
    If Me.lstVenta.ListCount = 0 Then
        MsgBox "No hay productos en la venta.", vbExclamation: Exit Sub
    End If

    Dim cliente As String: cliente = Me.cmbCliente.Text
    Dim numeroVentaActual As Long: numeroVentaActual = numeroVenta
    Dim filaVenta As Long: filaVenta = wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row + 1

    Dim ventaData() As Variant: ReDim ventaData(1 To Me.lstVenta.ListCount, 1 To 10)
    Dim i As Long
    For i = 0 To Me.lstVenta.ListCount - 1
        Dim codigo As String: codigo = Me.lstVenta.List(i, 0)
        Dim cantidad As Long: cantidad = CLng(Me.lstVenta.List(i, 2))
        Dim subtotal As Double: subtotal = LimpiarTextoPrecio(Me.lstVenta.List(i, 3))

        ventaData(i + 1, 1) = Date
        ventaData(i + 1, 2) = Time
        ventaData(i + 1, 3) = numeroVentaActual
        ventaData(i + 1, 4) = cliente
        ventaData(i + 1, 5) = codigo
        ventaData(i + 1, 6) = Replace(Me.lstVenta.List(i, 1), " [SIN STOCK]", "")
        ventaData(i + 1, 7) = subtotal / cantidad ' Precio Unitario
        ventaData(i + 1, 8) = cantidad
        ventaData(i + 1, 9) = subtotal
        ventaData(i + 1, 10) = IIf(InStr(1, Me.lstVenta.List(i, 1), "[SIN STOCK]") > 0, "Vendido sin stock", "ACTIVA")

        Call ActualizarExistencia(codigo, cantidad, "RESTAR")
    Next i

    wsVentas.Range("A" & filaVenta).Resize(Me.lstVenta.ListCount, 10).Value = ventaData

    Call GuardarFacturaAutomatica(numeroVentaActual, cliente, Date)

    MsgBox "Venta FAPOS" & Format(numeroVentaActual, "00000") & " registrada." & vbCrLf & "Total: " & Me.lblTotal.Caption, vbInformation, "Venta Exitosa"

    numeroVenta = numeroVentaActual + 1
    Call LimpiarVentaActual
    Call ActualizarResumenVentasDelDia
    Exit Sub
ErrorHandler:
    MsgBox "Error finalizando la venta: " & Err.Description, vbCritical
End Sub


' ==================================================
' PESTAÑA 1: HISTORIAL DE VENTAS
' ==================================================

Private Sub CargarHistorialVentas()
    On Error GoTo ErrorHandler
    Application.ScreenUpdating = False

    With Me.lstHistorial
        .Clear
        .ColumnCount = 7
        .ColumnWidths = "50;80;180;50;50;70;70"
        .AddItem "VENTA;ESTADO;CLIENTE;FECHA;ITEMS;ART.;TOTAL"
    End With

    Dim ultimaFila As Long: ultimaFila = wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row
    If ultimaFila < 2 Then
        Me.lstHistorial.AddItem ";;No hay ventas registradas"
        Me.lblTituloHistorial.Caption = "HISTORIAL - No hay ventas"
        Application.ScreenUpdating = True
        Exit Sub
    End If

    Dim ventasData As Variant: ventasData = wsVentas.Range("A2:J" & ultimaFila).Value
    Dim ventasUnicas As Object: Set ventasUnicas = CreateObject("Scripting.Dictionary")

    Dim i As Long
    For i = 1 To UBound(ventasData, 1)
        Dim numVenta As Long: numVenta = CLng(ventasData(i, 3))
        If Not ventasUnicas.Exists(numVenta) Then
            ventasUnicas.Add numVenta, Array(ventasData(i, 4), ventasData(i, 1), 0, 0, IIf(Trim(CStr(ventasData(i, 10))) = "ANULADA", "ANULADA", "ACTIVA"), CreateObject("Scripting.Dictionary"))
        End If
        Dim ventaActual As Variant: ventaActual = ventasUnicas(numVenta)
        If ventaActual(4) <> "ANULADA" Then ventaActual(2) = ventaActual(2) + CDbl(ventasData(i, 9))
        ventaActual(3) = ventaActual(3) + CLng(ventasData(i, 8))
        Dim codigoArticulo As String: codigoArticulo = CStr(ventasData(i, 5))
        If Not ventaActual(5).Exists(codigoArticulo) Then ventaActual(5).Add codigoArticulo, 1
        ventasUnicas(numVenta) = ventaActual
    Next i

    Dim ventaKeys As Variant: ventaKeys = ventasUnicas.Keys
    Dim k As Long, l As Long, tempKey As Variant
    For k = LBound(ventaKeys) To UBound(ventaKeys) - 1
        For l = k + 1 To UBound(ventaKeys)
            If CLng(ventaKeys(k)) < CLng(ventaKeys(l)) Then
                tempKey = ventaKeys(k): ventaKeys(k) = ventaKeys(l): ventaKeys(l) = tempKey
            End If
        Next l
    Next k

    Dim listData() As String: ReDim listData(0 To ventasUnicas.Count - 1, 0 To 6)
    Dim r As Long: r = -1
    For Each key In ventaKeys
        r = r + 1
        Dim datosVenta As Variant: datosVenta = ventasUnicas(key)
        listData(r, 0) = key
        listData(r, 1) = IIf(datosVenta(4) = "ANULADA", "** ANULADA **", "ACTIVA")
        listData(r, 2) = datosVenta(0)
        listData(r, 3) = Format(datosVenta(1), "dd/mm/yy")
        listData(r, 4) = datosVenta(3)
        listData(r, 5) = datosVenta(5).Count
        listData(r, 6) = IIf(datosVenta(4) = "ANULADA", FormatearPrecio(0), FormatearPrecio(datosVenta(2)))
    Next key

    Me.lstHistorial.List = listData
    Me.lblTituloHistorial.Caption = "HISTORIAL - " & ventasUnicas.Count & " ventas (Doble clic para ver detalles)"

    Application.ScreenUpdating = True
    Exit Sub
ErrorHandler:
    Application.ScreenUpdating = True
    MsgBox "Error al cargar el historial: " & Err.Description, vbCritical
End Sub

' ==================================================
' PESTAÑA 2: REPORTES
' ==================================================

Private Sub btnGenerarReporteDetallado_Click()
    Call GenerarReporteExcel
End Sub

Private Sub ActualizarDatosReportes()
    On Error GoTo ErrorHandler
    Dim ventaHoy As Double, ventaSemana As Double, ventaMes As Double
    Dim fila As Long, fechaVenta As Date, montoVenta As Double
    Dim ventasData As Variant, ultimaFila As Long

    ultimaFila = wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row
    If ultimaFila < 2 Then Exit Sub
    ventasData = wsVentas.Range("A2:J" & ultimaFila).Value

    For fila = 1 To UBound(ventasData, 1)
        If UCase(CStr(ventasData(fila, 10))) <> "ANULADA" Then
            fechaVenta = CDate(ventasData(fila, 1))
            montoVenta = CDbl(ventasData(fila, 9))
            If fechaVenta = Date Then ventaHoy = ventaHoy + montoVenta
            If fechaVenta >= (Date - 7) And fechaVenta <= Date Then ventaSemana = ventaSemana + montoVenta
            If Month(fechaVenta) = Month(Date) And Year(fechaVenta) = Year(Date) Then ventaMes = ventaMes + montoVenta
        End If
    Next fila

    ' Asegúrate de que los nombres de los controles sean correctos
    ' Me.lblVentaHoyReporte.Caption = "Venta de Hoy: " & FormatearPrecio(ventaHoy)
    ' Me.lblVentaSemana.Caption = "Última Semana: " & FormatearPrecio(ventaSemana)
    ' Me.lblVentaMes.Caption = "Mes Actual: " & FormatearPrecio(ventaMes)

    Call CargarTopProductos(ventasData)
    Exit Sub
ErrorHandler:
    MsgBox "Error actualizando reportes: " & Err.Description
End Sub

Private Sub CargarTopProductos(ByRef ventasData As Variant)
    Dim dictProductos As Object: Set dictProductos = CreateObject("Scripting.Dictionary")
    Dim fila As Long, producto As String, cantidad As Integer, monto As Double

    For fila = 1 To UBound(ventasData, 1)
        If UCase(CStr(ventasData(fila, 10))) <> "ANULADA" Then
            producto = CStr(ventasData(fila, 6))
            cantidad = CInt(ventasData(fila, 8))
            monto = CDbl(ventasData(fila, 9))
            If dictProductos.Exists(producto) Then
                dictProductos(producto)(0) = dictProductos(producto)(0) + cantidad
                dictProductos(producto)(1) = dictProductos(producto)(1) + monto
            Else
                dictProductos.Add producto, Array(cantidad, monto)
            End If
        End If
    Next fila

    With Me.lstTopProductos
        .Clear
        .ColumnCount = 3
        .ColumnWidths = "200;50;80"
    End With

    Dim listItems() As String
    ReDim listItems(0 To dictProductos.Count - 1, 0 To 2)
    Dim key As Variant, r As Long: r = 0
    For Each key In dictProductos.Keys
        listItems(r, 0) = Left(key, 30)
        listItems(r, 1) = dictProductos(key)(0)
        listItems(r, 2) = FormatearPrecio(dictProductos(key)(1))
        r = r + 1
    Next key

    ' Aquí se debería ordenar el array `listItems` antes de asignarlo, si se desea.
    Me.lstTopProductos.List = listItems
End Sub

' ==================================================
' PESTAÑA 3: AJUSTES DE INVENTARIO
' ==================================================

Private Sub txtBuscarAjuste_KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)
    If KeyAscii = 13 Then Call BuscarProductoAjuste: KeyAscii = 0
End Sub

Private Sub btnBuscarAjuste_Click()
    Call BuscarProductoAjuste
End Sub

Private Sub btnGuardarPrecio_Click()
    Call GuardarNuevoPrecio
End Sub

Private Sub BuscarProductoAjuste()
    On Error GoTo ErrorHandler
    Dim textoBusqueda As String: textoBusqueda = UCase(Trim(Me.txtBuscarAjuste.Text))
    With Me.lstProductosAjuste: .Clear: .ColumnCount = 4: .ColumnWidths = "80;200;70;0": End With
    If textoBusqueda = "" Then Exit Sub
    Dim resultados() As Variant, encontrados As Long: encontrados = 0, key As Variant, producto As Variant
    For Each key In ProductosEnMemoria.Keys
        producto = ProductosEnMemoria(key)
        If InStr(1, UCase(key), textoBusqueda) > 0 Or InStr(1, UCase(producto(0)), textoBusqueda) > 0 Then
            encontrados = encontrados + 1: ReDim Preserve resultados(1 To 4, 1 To encontrados)
            resultados(1, encontrados) = key: resultados(2, encontrados) = producto(0): resultados(3, encontrados) = FormatearPrecio(producto(1)): resultados(4, encontrados) = key
        End If
    Next key
    If encontrados > 0 Then
        Me.lstProductosAjuste.Column = resultados
        If encontrados = 1 Then Me.lstProductosAjuste.ListIndex = 0: Call lstProductosAjuste_Click
    Else
        Me.lstProductosAjuste.AddItem "No se encontraron productos"
    End If
    Exit Sub
ErrorHandler:
    MsgBox "Error al buscar para ajuste: " & Err.Description, vbExclamation
End Sub

Private Sub lstProductosAjuste_Click()
    If Me.lstProductosAjuste.ListIndex < 0 Then Exit Sub
    Dim codigo As String: codigo = Me.lstProductosAjuste.List(Me.lstProductosAjuste.ListIndex, 3)
    If ProductosEnMemoria.Exists(codigo) Then
        Dim producto As Variant: producto = ProductosEnMemoria(codigo)
        filaProductoActual = producto(3)
        Me.lblProductoEncontrado.Caption = "Producto: " & producto(0)
        Me.lblPrecioActual.Caption = "Precio Actual: " & FormatearPrecio(producto(1))
        Me.txtNuevoPrecio.Text = producto(1)
        Me.txtNuevoPrecio.SetFocus
    End If
End Sub

Private Sub GuardarNuevoPrecio()
    On Error GoTo ErrorHandler
    If filaProductoActual = 0 Then MsgBox "Seleccione un producto.", vbExclamation: Exit Sub

    Dim nuevoPrecio As Double: nuevoPrecio = CDbl(Me.txtNuevoPrecio.Text)
    If nuevoPrecio <= 0 Then MsgBox "Precio inválido.", vbExclamation: Exit Sub

    Dim codigo As String: codigo = wsProductos.Cells(filaProductoActual, 1).Value
    Dim precioAnterior As Double: precioAnterior = wsProductos.Cells(filaProductoActual, 6).Value

    If MsgBox("¿Actualizar precio de '" & wsProductos.Cells(filaProductoActual, 2).Value & "'?" & vbCrLf & "Anterior: " & FormatearPrecio(precioAnterior) & " -> Nuevo: " & FormatearPrecio(nuevoPrecio), vbYesNo + vbQuestion, "Confirmar") = vbYes Then
        wsProductos.Cells(filaProductoActual, 6).Value = nuevoPrecio
        wsProductos.Cells(filaProductoActual, 13).Value = "Cambio: " & Format(Now, "dd/mm/yy hh:mm")
        wsProductos.Cells(filaProductoActual, 14).Value = "De " & FormatearPrecio(precioAnterior) & " a " & FormatearPrecio(nuevoPrecio)

        Dim producto As Variant: producto = ProductosEnMemoria(codigo)
        producto(1) = nuevoPrecio
        ProductosEnMemoria(codigo) = producto

        MsgBox "Precio actualizado.", vbInformation
        filaProductoActual = 0
        Me.txtBuscarAjuste.Text = "": Me.txtNuevoPrecio.Text = ""
        Me.lblProductoEncontrado.Caption = "Producto:": Me.lblPrecioActual.Caption = "Precio Actual:"
        Me.lstProductosAjuste.Clear
    End If
    Exit Sub
ErrorHandler:
    MsgBox "Error al guardar precio: " & Err.Description, vbCritical
End Sub

' ==================================================
' RUTINAS DE SOPORTE Y UTILIDADES
' ==================================================

Private Sub CargarProductosEnMemoria()
    On Error GoTo ErrorHandler
    ProductosEnMemoria.RemoveAll
    Dim ultimaFila As Long: ultimaFila = wsProductos.Cells(wsProductos.Rows.Count, "A").End(xlUp).Row
    If ultimaFila < 3 Then Exit Sub

    Dim rangoProductos As Variant: rangoProductos = wsProductos.Range("A3:F" & ultimaFila).Value
    Dim i As Long
    For i = 1 To UBound(rangoProductos, 1)
        Dim codigo As String: codigo = CStr(rangoProductos(i, 1))
        If Not IsEmpty(codigo) And Not ProductosEnMemoria.Exists(codigo) Then
            ProductosEnMemoria.Add codigo, Array(rangoProductos(i, 2), CDbl(rangoProductos(i, 6)), CLng(rangoProductos(i, 5)), i + 2)
        End If
    Next i
    Exit Sub
ErrorHandler:
    MsgBox "Error fatal al cargar productos: " & Err.Description, vbCritical
End Sub

Private Sub CargarClientesComboBox()
    On Error GoTo ErrorHandler
    Me.cmbCliente.Clear
    Me.cmbCliente.AddItem "CONSUMIDOR FINAL"
    Dim ultimaFila As Long: ultimaFila = wsClientes.Cells(wsClientes.Rows.Count, "A").End(xlUp).Row
    If ultimaFila < 2 Then Exit Sub

    Dim rangoClientes As Variant: rangoClientes = wsClientes.Range("B2:B" & ultimaFila).Value
    Dim i As Long
    For i = 1 To UBound(rangoClientes, 1)
        If Not IsEmpty(rangoClientes(i, 1)) Then Me.cmbCliente.AddItem Trim(rangoClientes(i, 1))
    Next i
    Me.cmbCliente.ListIndex = 0
    Exit Sub
ErrorHandler:
    MsgBox "Error cargando clientes: " & Err.Description, vbExclamation
End Sub

Private Sub DeterminarNumeroSiguienteVenta()
    On Error Resume Next
    Dim ultimaFila As Long: ultimaFila = wsVentas.Cells(wsVentas.Rows.Count, "C").End(xlUp).Row
    If ultimaFila > 1 Then numeroVenta = wsVentas.Cells(ultimaFila, "C").Value + 1 Else numeroVenta = 1
End Sub

Private Sub CrearBackupAlCerrar()
    On Error GoTo ErrorHandler
    Dim rutaBackup As String: rutaBackup = "G:\Mi unidad\FARMACIA\BackupsCierreDiario\"
    If Dir(rutaBackup, vbDirectory) = "" Then
        MsgBox "Carpeta de backup no encontrada. Se omitirá el backup.", vbExclamation
        Exit Sub
    End If
    Dim nombreArchivo As String: nombreArchivo = "POS_Backup_" & Format(Date, "yyyy-mm-dd") & "_" & Format(Time, "HHmmss") & ".xlsm"
    ThisWorkbook.SaveCopyAs rutaBackup & nombreArchivo
    MsgBox "Backup creado exitosamente en:" & vbCrLf & rutaBackup & nombreArchivo, vbInformation, "Backup Exitoso"
    Exit Sub
ErrorHandler:
    MsgBox "Error al crear backup: " & Err.Description, vbCritical
End Sub

Private Sub ActualizarExistencia(ByVal codigo As String, ByVal cantidad As Long, ByVal operacion As String)
    On Error GoTo ErrorHandler
    If Not ProductosEnMemoria.Exists(codigo) Then Exit Sub

    Dim producto As Variant: producto = ProductosEnMemoria(codigo)
    Dim filaProducto As Long: filaProducto = producto(3)
    Dim nuevoStock As Long

    If UCase(operacion) = "RESTAR" Then
        nuevoStock = producto(2) - cantidad
    Else
        nuevoStock = producto(2) + cantidad
    End If

    wsProductos.Cells(filaProducto, 5).Value = nuevoStock
    producto(2) = nuevoStock
    ProductosEnMemoria(codigo) = producto
    Exit Sub
ErrorHandler:
    MsgBox "Error actualizando stock para '" & codigo & "': " & Err.Description, vbCritical
End Sub

Private Sub LimpiarVentaActual()
    Me.lstVenta.Clear
    Me.lblTotal.Caption = FormatearPrecio(0)
    Me.txtBuscar.Text = ""
    Me.txtCantidad.Text = "1"
    Me.cmbCliente.ListIndex = 0
    Me.lstProductos.Clear
    Me.txtValorUnd.Text = ""
    Me.txtBuscar.SetFocus
End Sub

Private Sub CalcularTotalVenta()
    Dim total As Double: total = 0
    Dim i As Long
    For i = 0 To Me.lstVenta.ListCount - 1
        total = total + LimpiarTextoPrecio(Me.lstVenta.List(i, 3))
    Next i
    Me.lblTotal.Caption = FormatearPrecio(total)
End Sub

Private Sub ActualizarResumenVentasDelDia()
    On Error Resume Next
    Dim ventaHoy As Double, cantidadVentas As Integer
    Dim ultimaFila As Long: ultimaFila = wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row
    If ultimaFila < 2 Then GoTo UpdateLabel

    Dim ventasData As Variant: ventasData = wsVentas.Range("A2:J" & ultimaFila).Value
    Dim i As Long
    For i = 1 To UBound(ventasData, 1)
        If CDate(ventasData(i, 1)) = Date And UCase(CStr(ventasData(i, 10))) <> "ANULADA" Then
            ventaHoy = ventaHoy + CDbl(ventasData(i, 9))
            If i = 1 Or ventasData(i, 3) <> ventasData(i - 1, 3) Then
                cantidadVentas = cantidadVentas + 1
            End If
        End If
    Next i
UpdateLabel:
    Me.lblVentasHoy.Caption = "VENTAS HOY: " & FormatearPrecio(ventaHoy) & " (" & cantidadVentas & " ventas)"
End Sub

Private Sub ConfigurarVisibilidadSegunPermisos()
    On Error Resume Next
    Dim esAdmin As Boolean: esAdmin = (ObtenerNivelUsuario() = "Administrador")
    ' Me.btnAdminUsuarios.Visible = esAdmin
    ' Ejemplo: Me.MultiPage1.Pages(3).Visible = esAdmin ' Ocultar pestaña de Ajustes
End Sub

Private Sub AplicarTemaVisualModerno()
    On Error Resume Next
    Me.BackColor = &HECF0F1
    Me.btnFinalizar.BackColor = &H71CC2E
    Me.btnAgregar.BackColor = &HDB9834
    Me.btnEliminar.BackColor = RGB(255, 220, 220)
    ' Me.btnCancelarVenta.BackColor = &H3C4CE7
    Me.lblTotal.BackColor = &H3BDBFF
    Me.lblVentasHoy.BackColor = RGB(0, 176, 80)
    Me.txtBuscar.BackColor = RGB(255, 255, 230)
End Sub

Private Sub ConfigurarIconosEnBotones()
    On Error Resume Next
    Me.btnFinalizar.Caption = "[OK] Finalizar"
    Me.btnAgregar.Caption = "[+] Agregar"
    Me.btnEliminar.Caption = "[X] Eliminar"
    Me.btnLimpiar.Caption = "[Esc] Limpiar"
    ' Me.btnHistorial.Caption = "[H] Historial"
    Me.btnBuscar.Caption = "[F] Buscar"
    Me.btnAnular.Caption = "[N] Anular"
End Sub

Private Function ObtenerNivelUsuario() As String
    On Error Resume Next
    ObtenerNivelUsuario = ThisWorkbook.Names("NivelUsuario").RefersToRange.Value
    If ObtenerNivelUsuario = "" Then ObtenerNivelUsuario = "Administrador" ' Valor por defecto para pruebas
End Function

Private Sub GuardarFacturaAutomatica(ByVal numVenta As Long, ByVal cliente As String, ByVal fecha As Date)
    On Error GoTo ErrorHandler

    Dim rutaBase As String: rutaBase = ThisWorkbook.Path & "\FacturasIMP"
    If Dir(rutaBase, vbDirectory) = "" Then MkDir rutaBase

    Dim rutaAnio As String: rutaAnio = rutaBase & "\" & Year(fecha)
    If Dir(rutaAnio, vbDirectory) = "" Then MkDir rutaAnio

    Dim rutaMes As String: rutaMes = rutaAnio & "\" & Format(fecha, "mm-mmmm")
    If Dir(rutaMes, vbDirectory) = "" Then MkDir rutaMes

    Dim clienteLimpio As String: clienteLimpio = Replace(Replace(cliente, "/", "-"), "\", "-")

    Dim nombreArchivo As String
    nombreArchivo = "FAPOS" & Format(numVenta, "00000") & "_" & Format(fecha, "ddmmyyyy") & "_" & Left(clienteLimpio, 20) & ".pdf"

    Dim rutaPDF As String: rutaPDF = rutaMes & "\" & nombreArchivo

    Dim wsTemp As Worksheet: Set wsTemp = ThisWorkbook.Sheets.Add

    Call GenerarFacturaTirilla(wsTemp, numVenta)

    wsTemp.ExportAsFixedFormat Type:=xlTypePDF, Filename:=rutaPDF, Quality:=xlQualityStandard, OpenAfterPublish:=False

    Application.DisplayAlerts = False
    wsTemp.Delete
    Application.DisplayAlerts = True
    Exit Sub
ErrorHandler:
    MsgBox "No se pudo generar el PDF automático.", vbExclamation
    If Not wsTemp Is Nothing Then Application.DisplayAlerts = False: wsTemp.Delete: Application.DisplayAlerts = True
End Sub

Private Sub GenerarFacturaTirilla(ws As Worksheet, numeroVenta As Long)
    ' Esta es la lógica de formato de tu factura original.
    ' Se ha mantenido para preservar el diseño exacto.
    On Error Resume Next

    Dim fila As Long, filaFactura As Long
    Dim totalVenta As Double
    Dim cliente As String, fecha As String, hora As String

    ws.Cells.Clear

    For fila = 2 To wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row
        If wsVentas.Cells(fila, 3).Value = numeroVenta Then
            cliente = wsVentas.Cells(fila, 4).Value
            fecha = Format(wsVentas.Cells(fila, 1).Value, "dd/mm/yyyy")
            hora = Format(wsVentas.Cells(fila, 2).Value, "hh:mm:ss")
            Exit For
        End If
    Next fila

    ws.Cells.NumberFormat = "@"
    ws.Columns("A:A").ColumnWidth = 48
    ws.Cells.Font.Name = "Courier New"
    ws.Cells.Font.Size = 9

    filaFactura = 1
    ws.Cells(filaFactura, 1).Value = " CONSUELO RESTREPO PULGARIN": ws.Cells(filaFactura, 1).Font.Bold = True: ws.Cells(filaFactura, 1).Font.Size = 11
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "         NIT: 21.401.990"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "    CR 80 53 A 16 Los Colores"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "       Tel: 319 3790165"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "================================"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "Factura: FAPOS" & Format(numeroVenta, "00000"): ws.Cells(filaFactura, 1).Font.Bold = True
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "Fecha: " & fecha & " " & hora
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "Cliente: " & Left(cliente, 25)
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "NIT/ID: 222.222.222"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "================================"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "CANT  PRODUCTO": ws.Cells(filaFactura, 1).Font.Bold = True
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "      P.UNIT        SUBTOTAL": ws.Cells(filaFactura, 1).Font.Bold = True
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "--------------------------------"

    totalVenta = 0
    For fila = 2 To wsVentas.Cells(wsVentas.Rows.Count, "A").End(xlUp).Row
        If wsVentas.Cells(fila, 3).Value = numeroVenta Then
            Dim nombreProd As String, cant As Integer, precioUnit As Double, subtotal As Double
            nombreProd = Left(wsVentas.Cells(fila, 6).Value, 28): cant = wsVentas.Cells(fila, 8).Value
            precioUnit = wsVentas.Cells(fila, 7).Value: subtotal = wsVentas.Cells(fila, 9).Value
            filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = Format(cant, "00") & "  " & nombreProd
            filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "    $" & Format(precioUnit, "#,##0") & "      $" & Format(subtotal, "#,##0")
            totalVenta = totalVenta + subtotal
        End If
    Next fila

    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "================================"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "TOTAL:           $" & Format(totalVenta, "#,##0"): ws.Cells(filaFactura, 1).Font.Bold = True: ws.Cells(filaFactura, 1).Font.Size = 11
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "================================"
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "PERSONA NATURAL NO RESPONSABLE DE IVA": ws.Cells(filaFactura, 1).Font.Size = 7
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "SUJETO NO OBLIGADO A EXPEDIR FACTURA": ws.Cells(filaFactura, 1).Font.Size = 7
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = "ELECTRÓNICA NI DOCUMENTO EQUIVALENTE": ws.Cells(filaFactura, 1).Font.Size = 7
    filaFactura = filaFactura + 1: ws.Cells(filaFactura, 1).Value = " ¡Gracias por su compra!": ws.Cells(filaFactura, 1).Font.Italic = True

    With ws.PageSetup: .PrintArea = "$A$1:$A$" & filaFactura: .PaperSize = xlPaperUser: .Orientation = xlPortrait: .Zoom = False: .FitToPagesWide = 1: .FitToPagesTall = False: End With
End Sub

Private Sub GenerarReporteExcel()
    MsgBox "La funcionalidad de generar reporte detallado en Excel aún no ha sido implementada en esta versión optimizada.", vbInformation
End Sub