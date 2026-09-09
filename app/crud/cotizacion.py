from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionDetalle
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.comprobante import Comprobante
from app.models.estado import Estado
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.models.producto_unidad import ProductoUnidad
from app.models.unidad_medida import UnidadMedida
from app.schemas.cotizacion import CotizacionCreate, CotizacionUpdate, ConvertirVentaRequest
from app.utils import capitalizar, a_mayusculas
from app.crud.venta import _validar_stock_para_venta, _update_stock

IVA_RATE = Decimal("13")
IT_RATE = Decimal("3")
ESTADO_ENVIADO = "Enviado"
ESTADO_CONFIRMADO = "Confirmado"
ESTADO_VENCIDO = "Vencido"


def _q(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _precio_venta(costo: Decimal, utilidad_pct: Decimal, con_factura: bool = False) -> Decimal:
    costo = Decimal(costo or 0)
    pct = Decimal(utilidad_pct or 0)
    precio = costo + (costo * pct / 100)
    if con_factura:
        precio = precio * (Decimal("1") + IVA_RATE / 100) * (Decimal("1") + IT_RATE / 100)
    return _q(precio)


def _marcar_vencidas(db: Session):
    ahora = datetime.now()
    vencidas = db.query(Cotizacion).filter(
        Cotizacion.estado == ESTADO_ENVIADO,
        Cotizacion.fecha_vencimiento < ahora,
        Cotizacion.activo == True,
    ).all()
    for cot in vencidas:
        cot.estado = ESTADO_VENCIDO
    if vencidas:
        db.commit()


def _validate_foreign_keys(db: Session, cliente_id: int, detalles: list):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail=f"Cliente {cliente_id} no existe")

    for detalle in detalles:
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if not producto:
            raise HTTPException(status_code=400, detail=f"Producto {detalle.producto_id} no existe")
        if not detalle.cantidad or Decimal(detalle.cantidad) < Decimal("0.01"):
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {detalle.producto_id}")
        if Decimal(detalle.costo or 0) < 0:
            raise HTTPException(status_code=400, detail=f"Costo inválido para el producto {detalle.producto_id}")
        if Decimal(detalle.utilidad_pct or 0) < 0:
            raise HTTPException(status_code=400, detail=f"Utilidad inválida para el producto {detalle.producto_id}")
        if getattr(detalle, "unidad_id", None):
            pu = db.query(ProductoUnidad).filter(
                ProductoUnidad.producto_id == detalle.producto_id,
                ProductoUnidad.unidad_id == detalle.unidad_id,
            ).first()
            if not pu:
                raise HTTPException(status_code=400, detail=f"Unidad {detalle.unidad_id} no registrada en el producto {detalle.producto_id}")


def _get_estado_por_nombre(db: Session, nombre: str):
    estado = db.query(Estado).filter(Estado.nombre == nombre).first()
    if not estado:
        estado = Estado(nombre=nombre)
        db.add(estado)
        db.flush()
    return estado


def _get_unidad_info(db: Session, producto_id: int, unidad_id: int = None):
    if unidad_id:
        pu = db.query(ProductoUnidad).filter(
            ProductoUnidad.producto_id == producto_id,
            ProductoUnidad.unidad_id == unidad_id,
        ).first()
        if pu:
            u = db.query(UnidadMedida).filter(UnidadMedida.id == unidad_id).first()
            return {
                "pu": pu,
                "unidad_nombre": u.nombre if u else "",
                "unidad_abreviatura": u.abreviatura if u else "",
                "factor": pu.factor_conversion or Decimal("1"),
                "es_principal": bool(pu.es_principal),
            }
    pu = db.query(ProductoUnidad).filter(
        ProductoUnidad.producto_id == producto_id,
        ProductoUnidad.es_principal == True,
    ).first()
    if pu:
        u = db.query(UnidadMedida).filter(UnidadMedida.id == pu.unidad_id).first()
        return {
            "pu": pu,
            "unidad_nombre": u.nombre if u else "",
            "unidad_abreviatura": u.abreviatura if u else "",
            "factor": Decimal("1"),
            "es_principal": True,
        }
    return {
        "pu": None,
        "unidad_nombre": "",
        "unidad_abreviatura": "",
        "factor": Decimal("1"),
        "es_principal": True,
    }


def _build_response(db: Session, cot: Cotizacion):
    detalles = db.query(CotizacionDetalle).options(
        selectinload(CotizacionDetalle.producto)
    ).filter(CotizacionDetalle.cotizacion_id == cot.id).all()

    detalles_response = []
    for d in detalles:
        prod = d.producto
        cat_nombre = ""
        if prod and prod.categoria:
            cat_nombre = prod.categoria.nombre
        stock_actual = prod.stock_actual if prod else 0
        uinfo = _get_unidad_info(db, d.producto_id, d.unidad_id)
        factor = uinfo["factor"]
        cantidad_principal = _q(Decimal(d.cantidad) * factor) if factor > 0 else Decimal(d.cantidad)

        detalles_response.append({
            "id": d.id,
            "producto_id": d.producto_id,
            "producto_nombre": prod.descripcion if prod else "",
            "producto_codigo": prod.codigo if prod else "",
            "producto_categoria": cat_nombre,
            "producto_imagen": prod.imagen if prod else None,
            "unidad_id": d.unidad_id,
            "unidad_nombre": uinfo["unidad_nombre"],
            "unidad_abreviatura": uinfo["unidad_abreviatura"],
            "es_principal": uinfo["es_principal"],
            "factor_conversion": factor,
            "cantidad": d.cantidad,
            "costo": d.costo,
            "utilidad_pct": d.utilidad_pct,
            "precio_venta": d.precio_venta,
            "stock_actual": stock_actual,
            "cantidad_principal": cantidad_principal,
        })

    usuario = db.query(Usuario).filter(Usuario.id == cot.usuario_id).first()

    return {
        "id": cot.id,
        "numero": cot.numero,
        "fecha": cot.fecha,
        "fecha_vencimiento": cot.fecha_vencimiento,
        "cliente_id": cot.cliente_id,
        "cliente_razon_social": cot.cliente_razon_social or "",
        "cliente_nit": cot.cliente_nit or "",
        "cliente_celular": cot.cliente_celular or "",
        "cliente_direccion": cot.cliente_direccion or "",
        "estado": cot.estado,
        "con_factura": bool(cot.con_factura),
        "incluir_imagenes": bool(cot.incluir_imagenes),
        "modalidad_pago": cot.modalidad_pago or "",
        "forma_pago": cot.forma_pago or "",
        "validez_dias": cot.validez_dias or 0,
        "terminos_condiciones": cot.terminos_condiciones or "",
        "subtotal": cot.subtotal or 0,
        "iva": cot.iva or 0,
        "it": cot.it or 0,
        "descuento": cot.descuento or 0,
        "total": cot.total or 0,
        "activo": bool(cot.activo),
        "usuario_id": cot.usuario_id,
        "usuario_username": usuario.username if usuario else "",
        "venta_id": cot.venta_id,
        "fecha_registro": cot.fecha_registro,
        "detalles": detalles_response,
    }


def get_cotizacion(db: Session, cotizacion_id: int):
    _marcar_vencidas(db)
    cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not cot:
        return None
    return _build_response(db, cot)


def get_cotizaciones(db: Session, skip: int = 0, limit: int = 100):
    _marcar_vencidas(db)
    cotizaciones = db.query(Cotizacion).filter(Cotizacion.activo == True).order_by(Cotizacion.id.desc()).offset(skip).limit(limit).all()
    return [_build_response(db, c) for c in cotizaciones]


def _calcular_totales(cot, con_factura: bool):
    subtotal = Decimal("0")
    for d in cot.detalles:
        subtotal += Decimal(d.cantidad) * Decimal(d.precio_venta)
    subtotal = _q(subtotal)
    iva = _q(subtotal * IVA_RATE / 100) if con_factura else Decimal("0.00")
    it = _q(subtotal * IT_RATE / 100) if con_factura else Decimal("0.00")
    descuento_monto = _q(subtotal * (cot.descuento or 0) / 100)
    total = _q(subtotal - descuento_monto)
    return subtotal, iva, it, descuento_monto, total


def _fecha_hora(fecha: datetime) -> datetime:
    fecha = fecha if isinstance(fecha, datetime) else datetime.combine(fecha, datetime.min.time())
    return datetime.combine(fecha.date(), datetime.now().time())


def _resolve_costo_por_unidad(db: Session, producto_id: int, unidad_id: int, costo_enviado: Decimal) -> Decimal:
    # El frontend envía costo_base = costo de 1 unidad principal.
    # El costo de la línea en su unidad = costo_base * factor
    #   (principal factor 1 -> mismo; secundaria caja factor 10 -> x10)
    uinfo = _get_unidad_info(db, producto_id, unidad_id)
    factor = uinfo["factor"]
    return _q(Decimal(costo_enviado) * factor) if factor > 0 else _q(costo_enviado)


def create_cotizacion(db: Session, cot: CotizacionCreate, usuario_id: int):
    _validate_foreign_keys(db, cot.cliente_id, cot.detalles)
    if not cot.detalles:
        raise HTTPException(status_code=400, detail="Debe agregar al menos un producto")

    cliente = db.query(Cliente).filter(Cliente.id == cot.cliente_id).first()

    fecha = _fecha_hora(cot.fecha)
    fecha_vencimiento = fecha + timedelta(days=int(cot.validez_dias or 15))

    db_cot = Cotizacion(
        numero=f"COT-{uuid4().hex[:10].upper()}",
        fecha=fecha,
        fecha_vencimiento=fecha_vencimiento,
        cliente_id=cot.cliente_id,
        estado=ESTADO_ENVIADO,
        con_factura=bool(cot.con_factura),
        incluir_imagenes=bool(cot.incluir_imagenes),
        modalidad_pago=capitalizar(cot.modalidad_pago or ""),
        forma_pago=cot.forma_pago or "",
        validez_dias=int(cot.validez_dias or 15),
        terminos_condiciones=capitalizar(cot.terminos_condiciones or ""),
        descuento=_q(cot.descuento),
        usuario_id=usuario_id,
        activo=True,
        cliente_razon_social=a_mayusculas(cliente.nombre) if cliente else "",
        cliente_nit=cliente.nit if cliente else "",
        cliente_celular=cliente.celular if cliente else "",
        cliente_direccion=capitalizar(cliente.direccion) if cliente else "",
    )
    db.add(db_cot)
    db.flush()

    db_cot.numero = f"COT-{db_cot.id:06d}"

    for detalle in cot.detalles:
        costo_por_unidad = _resolve_costo_por_unidad(db, detalle.producto_id, detalle.unidad_id, detalle.costo)
        db_detalle = CotizacionDetalle(
            cotizacion_id=db_cot.id,
            producto_id=detalle.producto_id,
            unidad_id=detalle.unidad_id,
            cantidad=Decimal(detalle.cantidad),
            costo=costo_por_unidad,
            utilidad_pct=_q(detalle.utilidad_pct),
            precio_venta=_precio_venta(costo_por_unidad, detalle.utilidad_pct, bool(cot.con_factura)),
        )
        db.add(db_detalle)

    db.flush()
    db_cot.subtotal, db_cot.iva, db_cot.it, _, db_cot.total = _calcular_totales(db_cot, bool(cot.con_factura))

    db.commit()
    db.refresh(db_cot)
    return _build_response(db, db_cot)


def update_cotizacion(db: Session, cotizacion_id: int, cot: CotizacionUpdate):
    db_cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cot:
        return None
    if db_cot.estado != ESTADO_ENVIADO:
        raise HTTPException(status_code=400, detail="Solo se pueden editar cotizaciones en estado Enviado")
    if db_cot.venta_id:
        raise HTTPException(status_code=400, detail="No se puede editar una cotización convertida en venta")

    cliente_id = cot.cliente_id if cot.cliente_id is not None else db_cot.cliente_id

    if cot.fecha is not None:
        fecha = _fecha_hora(cot.fecha)
        db_cot.fecha = fecha
    if cot.cliente_id is not None:
        db_cot.cliente_id = cot.cliente_id
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            db_cot.cliente_razon_social = a_mayusculas(cliente.nombre)
            db_cot.cliente_nit = cliente.nit
            db_cot.cliente_celular = cliente.celular
            db_cot.cliente_direccion = capitalizar(cliente.direccion)
    if cot.con_factura is not None:
        db_cot.con_factura = bool(cot.con_factura)
    if cot.incluir_imagenes is not None:
        db_cot.incluir_imagenes = bool(cot.incluir_imagenes)
    if cot.modalidad_pago is not None:
        db_cot.modalidad_pago = capitalizar(cot.modalidad_pago)
    if cot.forma_pago is not None:
        db_cot.forma_pago = cot.forma_pago
    if cot.descuento is not None:
        db_cot.descuento = _q(cot.descuento)
    if cot.validez_dias is not None:
        db_cot.validez_dias = int(cot.validez_dias)
        db_cot.fecha_vencimiento = db_cot.fecha + timedelta(days=int(cot.validez_dias))
    if cot.terminos_condiciones is not None:
        db_cot.terminos_condiciones = capitalizar(cot.terminos_condiciones)

    if cot.detalles is not None:
        if not cot.detalles:
            raise HTTPException(status_code=400, detail="Debe agregar al menos un producto")
        _validate_foreign_keys(db, cliente_id, cot.detalles)
        db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion_id).delete()
        for detalle in cot.detalles:
            costo_por_unidad = _resolve_costo_por_unidad(db, detalle.producto_id, detalle.unidad_id, detalle.costo)
            db_detalle = CotizacionDetalle(
                cotizacion_id=cotizacion_id,
                producto_id=detalle.producto_id,
                unidad_id=detalle.unidad_id,
                cantidad=Decimal(detalle.cantidad),
                costo=costo_por_unidad,
                utilidad_pct=_q(detalle.utilidad_pct),
                precio_venta=_precio_venta(costo_por_unidad, detalle.utilidad_pct, bool(db_cot.con_factura)),
            )
            db.add(db_detalle)

    db.flush()
    db_cot.subtotal, db_cot.iva, db_cot.it, _, db_cot.total = _calcular_totales(db_cot, bool(db_cot.con_factura))

    db.commit()
    db.refresh(db_cot)
    return _build_response(db, db_cot)


def confirmar_cotizacion(db: Session, cotizacion_id: int):
    db_cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cot:
        return None
    if db_cot.estado == ESTADO_CONFIRMADO:
        raise HTTPException(status_code=400, detail="La cotización ya está confirmada")
    if db_cot.estado == ESTADO_VENCIDO:
        raise HTTPException(status_code=400, detail="No se puede confirmar una cotización vencida")
    if db_cot.estado != ESTADO_ENVIADO:
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar cotizaciones enviadas")

    db_cot.estado = ESTADO_CONFIRMADO
    db.commit()
    db.refresh(db_cot)
    return _build_response(db, db_cot)


def delete_cotizacion(db: Session, cotizacion_id: int):
    db_cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cot:
        return None
    if db_cot.venta_id:
        raise HTTPException(status_code=400, detail="No se puede eliminar una cotización convertida en venta")
    if db_cot.estado == ESTADO_CONFIRMADO:
        raise HTTPException(status_code=400, detail="No se puede eliminar una cotización confirmada")

    db_cot.activo = False
    db.commit()
    db.refresh(db_cot)
    return _build_response(db, db_cot)


def convertir_en_venta(db: Session, cotizacion_id: int, payload: ConvertirVentaRequest, usuario_id: int):
    db_cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cot:
        return None
    if db_cot.estado != ESTADO_CONFIRMADO:
        raise HTTPException(status_code=400, detail="Solo se puede convertir en venta una cotización confirmada")
    if db_cot.venta_id:
        raise HTTPException(status_code=400, detail="Esta cotización ya fue convertida en venta")

    detalles = db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion_id).all()
    if not detalles:
        raise HTTPException(status_code=400, detail="La cotización no tiene productos")

    comprobante = db.query(Comprobante).filter(Comprobante.id == payload.comprobante_id).first()
    if not comprobante:
        raise HTTPException(status_code=400, detail=f"Comprobante {payload.comprobante_id} no existe")

    if payload.estado_id is not None:
        estado = db.query(Estado).filter(Estado.id == payload.estado_id).first()
        if not estado:
            raise HTTPException(status_code=400, detail=f"Estado {payload.estado_id} no existe")
        estado_id = payload.estado_id
    else:
        estado_pendiente = _get_estado_por_nombre(db, "Pendiente")
        estado_id = estado_pendiente.id

    try:
        # El stock se gestiona en la unidad principal: convertir cada cantidad
        # de la línea (en su unidad) a cantidad en unidades principales antes de validar.
        from types import SimpleNamespace
        detalles_en_principal = []
        for d in detalles:
            uinfo = _get_unidad_info(db, d.producto_id, d.unidad_id)
            factor = uinfo["factor"]
            cant_principal = Decimal(d.cantidad) * factor if factor > 0 else Decimal(d.cantidad)
            detalles_en_principal.append(SimpleNamespace(producto_id=d.producto_id, cantidad=cant_principal))
        _validar_stock_para_venta(db, detalles_en_principal)

        if payload.automatico:
            comprobante = db.query(Comprobante).filter(Comprobante.id == payload.comprobante_id).with_for_update().first()
            num_comprobante = payload.num_comprobante or str(comprobante.numero).zfill(8)
            comprobante.numero += 1
        else:
            num_comprobante = payload.num_comprobante or ''

        impuesto = IVA_RATE if bool(db_cot.con_factura) else Decimal("0")
        it = IT_RATE if bool(db_cot.con_factura) else Decimal("0")
        descuento = _q(db_cot.descuento or Decimal("0"))

        # El stock y los montos se gestionan SIEMPRE en la unidad principal:
        #   cantidad_principal = cantidad (en su unidad) * factor  -> nro de unidades principales
        #   precio por unidad principal = precio_venta (de la cotización, ya calculado) / factor
        # El total de la venta se calcula desde las líneas convertidas (precios preservados),
        # SIN volver a aplicar la fórmula compuesta de IVA/IT.
        converted = []
        subtotal = Decimal("0")
        for d in detalles:
            uinfo = _get_unidad_info(db, d.producto_id, d.unidad_id)
            factor = uinfo["factor"]
            cantidad_principal = _q(Decimal(d.cantidad) * factor) if factor > 0 else Decimal(d.cantidad)
            precio_venta_principal = _q(Decimal(d.precio_venta) / factor) if factor > 0 else Decimal(d.precio_venta)
            utilidad = _q(Decimal(d.costo) * Decimal(d.utilidad_pct) / 100)
            converted.append((d, cantidad_principal, precio_venta_principal, utilidad))
            subtotal += _q(int(cantidad_principal) * precio_venta_principal)

        subtotal = _q(subtotal)
        total = _q(subtotal - _q(subtotal * descuento / 100))

        db_venta = Venta(
            fecha=datetime.combine(db_cot.fecha.date(), datetime.now().time()),
            cliente_id=db_cot.cliente_id,
            comprobante_id=payload.comprobante_id,
            num_comprobante=num_comprobante,
            estado_id=estado_id,
            total=total,
            impuesto=impuesto,
            it=it,
            descuento=descuento,
            usuario_id=usuario_id,
            activo=1 if estado_id == 3 else 0,
        )
        db.add(db_venta)
        db.flush()

        for d, cantidad_principal, precio_venta_principal, utilidad in converted:
            db_detalle = VentaDetalle(
                venta_id=db_venta.id,
                producto_id=d.producto_id,
                cantidad=int(cantidad_principal),
                precio=precio_venta_principal,
                utilidad=utilidad,
            )
            db.add(db_detalle)
            _update_stock(db, d.producto_id, int(cantidad_principal), sumar=False)

        db_cot.venta_id = db_venta.id
        db.commit()
        db.refresh(db_venta)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    from app.crud.venta import _build_response as _build_venta_response
    return _build_venta_response(db, db_venta)
