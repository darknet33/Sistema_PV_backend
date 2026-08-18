from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionDetalle
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.models.comprobante import Comprobante
from app.models.estado import Estado
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.schemas.cotizacion import CotizacionCreate, CotizacionUpdate, ConvertirVentaRequest
from app.crud.venta import _validar_stock_para_venta, _update_stock

IVA_RATE = Decimal("16")
ESTADO_ENVIADO = "Enviado"
ESTADO_CONFIRMADO = "Confirmado"
ESTADO_VENCIDO = "Vencido"


def _q(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _precio_venta(costo: Decimal, utilidad_pct: Decimal) -> Decimal:
    costo = Decimal(costo or 0)
    pct = Decimal(utilidad_pct or 0)
    return _q(costo + (costo * pct / 100))


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
        if not detalle.cantidad or int(detalle.cantidad) < 1:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {detalle.producto_id}")
        if Decimal(detalle.costo or 0) < 0:
            raise HTTPException(status_code=400, detail=f"Costo inválido para el producto {detalle.producto_id}")
        if Decimal(detalle.utilidad_pct or 0) < 0:
            raise HTTPException(status_code=400, detail=f"Utilidad inválida para el producto {detalle.producto_id}")


def _get_estado_por_nombre(db: Session, nombre: str):
    estado = db.query(Estado).filter(Estado.nombre == nombre).first()
    if not estado:
        estado = Estado(nombre=nombre)
        db.add(estado)
        db.flush()
    return estado


def _build_response(db: Session, cot: Cotizacion):
    detalles = db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cot.id).all()

    detalles_response = []
    for d in detalles:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ""
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ""
        detalles_response.append({
            "id": d.id,
            "producto_id": d.producto_id,
            "producto_nombre": prod.descripcion if prod else "",
            "producto_codigo": prod.codigo if prod else "",
            "producto_categoria": cat_nombre,
            "producto_imagen": prod.imagen if prod else None,
            "cantidad": d.cantidad,
            "costo": d.costo,
            "utilidad_pct": d.utilidad_pct,
            "precio_venta": d.precio_venta,
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
    descuento_monto = _q(subtotal * (cot.descuento or 0) / 100)
    total = _q(subtotal + iva - descuento_monto)
    return subtotal, iva, descuento_monto, total


def _fecha_hora(fecha: datetime) -> datetime:
    fecha = fecha if isinstance(fecha, datetime) else datetime.combine(fecha, datetime.min.time())
    return datetime.combine(fecha.date(), datetime.now().time())


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
        modalidad_pago=cot.modalidad_pago or "",
        forma_pago=cot.forma_pago or "",
        validez_dias=int(cot.validez_dias or 15),
        terminos_condiciones=cot.terminos_condiciones or "",
        descuento=_q(cot.descuento),
        usuario_id=usuario_id,
        activo=True,
        cliente_razon_social=cliente.nombre if cliente else "",
        cliente_nit=cliente.nit if cliente else "",
        cliente_celular=cliente.celular if cliente else "",
        cliente_direccion=cliente.direccion if cliente else "",
    )
    db.add(db_cot)
    db.flush()

    db_cot.numero = f"COT-{db_cot.id:06d}"

    for detalle in cot.detalles:
        db_detalle = CotizacionDetalle(
            cotizacion_id=db_cot.id,
            producto_id=detalle.producto_id,
            cantidad=int(detalle.cantidad),
            costo=_q(detalle.costo),
            utilidad_pct=_q(detalle.utilidad_pct),
            precio_venta=_precio_venta(detalle.costo, detalle.utilidad_pct),
        )
        db.add(db_detalle)

    db.flush()
    db_cot.subtotal, db_cot.iva, _, db_cot.total = _calcular_totales(db_cot, bool(cot.con_factura))

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
            db_cot.cliente_razon_social = cliente.nombre
            db_cot.cliente_nit = cliente.nit
            db_cot.cliente_celular = cliente.celular
            db_cot.cliente_direccion = cliente.direccion
    if cot.con_factura is not None:
        db_cot.con_factura = bool(cot.con_factura)
    if cot.incluir_imagenes is not None:
        db_cot.incluir_imagenes = bool(cot.incluir_imagenes)
    if cot.modalidad_pago is not None:
        db_cot.modalidad_pago = cot.modalidad_pago
    if cot.forma_pago is not None:
        db_cot.forma_pago = cot.forma_pago
    if cot.descuento is not None:
        db_cot.descuento = _q(cot.descuento)
    if cot.validez_dias is not None:
        db_cot.validez_dias = int(cot.validez_dias)
        db_cot.fecha_vencimiento = db_cot.fecha + timedelta(days=int(cot.validez_dias))
    if cot.terminos_condiciones is not None:
        db_cot.terminos_condiciones = cot.terminos_condiciones

    if cot.detalles is not None:
        if not cot.detalles:
            raise HTTPException(status_code=400, detail="Debe agregar al menos un producto")
        _validate_foreign_keys(db, cliente_id, cot.detalles)
        db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion_id).delete()
        for detalle in cot.detalles:
            db_detalle = CotizacionDetalle(
                cotizacion_id=cotizacion_id,
                producto_id=detalle.producto_id,
                cantidad=int(detalle.cantidad),
                costo=_q(detalle.costo),
                utilidad_pct=_q(detalle.utilidad_pct),
                precio_venta=_precio_venta(detalle.costo, detalle.utilidad_pct),
            )
            db.add(db_detalle)

    db.flush()
    db_cot.subtotal, db_cot.iva, _, db_cot.total = _calcular_totales(db_cot, bool(db_cot.con_factura))

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
        _validar_stock_para_venta(db, detalles)

        if payload.automatico:
            comprobante = db.query(Comprobante).filter(Comprobante.id == payload.comprobante_id).with_for_update().first()
            num_comprobante = payload.num_comprobante or str(comprobante.numero).zfill(8)
            comprobante.numero += 1
        else:
            num_comprobante = payload.num_comprobante or ''

        impuesto = IVA_RATE if bool(db_cot.con_factura) else Decimal("0")
        descuento = _q(db_cot.descuento or Decimal("0"))

        subtotal = sum(Decimal(d.cantidad) * Decimal(d.precio_venta) for d in detalles)
        total = _q(subtotal + (subtotal * impuesto / 100) - (subtotal * descuento / 100))

        db_venta = Venta(
            fecha=datetime.combine(db_cot.fecha.date(), datetime.now().time()),
            cliente_id=db_cot.cliente_id,
            comprobante_id=payload.comprobante_id,
            num_comprobante=num_comprobante,
            estado_id=estado_id,
            total=total,
            impuesto=impuesto,
            descuento=descuento,
            usuario_id=usuario_id,
            activo=1 if estado_id == 3 else 0,
        )
        db.add(db_venta)
        db.flush()

        for d in detalles:
            utilidad = _q(Decimal(d.costo) * Decimal(d.utilidad_pct) / 100)
            db_detalle = VentaDetalle(
                venta_id=db_venta.id,
                producto_id=d.producto_id,
                cantidad=d.cantidad,
                precio=d.precio_venta,
                utilidad=utilidad,
            )
            db.add(db_detalle)
            _update_stock(db, d.producto_id, d.cantidad, sumar=False)

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
