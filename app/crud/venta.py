from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.comprobante import Comprobante
from app.models.estado import Estado
from app.models.categoria import Categoria
from app.schemas.venta import VentaCreate, VentaUpdate

def _validate_foreign_keys(db: Session, cliente_id: int, comprobante_id: int, estado_id: int, detalles: list):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail=f"Cliente {cliente_id} no existe")

    comprobante = db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
    if not comprobante:
        raise HTTPException(status_code=400, detail=f"Comprobante {comprobante_id} no existe")

    estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if not estado:
        raise HTTPException(status_code=400, detail=f"Estado {estado_id} no existe")

    for detalle in detalles:
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if not producto:
            raise HTTPException(status_code=400, detail=f"Producto {detalle.producto_id} no existe")

def _update_stock(db: Session, producto_id: int, cantidad: int, sumar: bool):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        if sumar:
            producto.stock_actual = (producto.stock_actual or 0) + cantidad
        else:
            producto.stock_actual = max(0, (producto.stock_actual or 0) - cantidad)

def _build_response(db: Session, venta: Venta):
    cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first()
    comprobante = db.query(Comprobante).filter(Comprobante.id == venta.comprobante_id).first()
    estado = db.query(Estado).filter(Estado.id == venta.estado_id).first()
    detalles = db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta.id).all()

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
            "cantidad": d.cantidad,
            "precio": d.precio,
            "utilidad": d.utilidad,
        })

    return {
        "id": venta.id,
        "fecha": venta.fecha,
        "cliente_id": venta.cliente_id,
        "cliente_nombre": cliente.nombre if cliente else "",
        "comprobante_id": venta.comprobante_id,
        "comprobante_nombre": comprobante.nombre if comprobante else "",
        "num_comprobante": venta.num_comprobante,
        "estado_id": venta.estado_id,
        "estado_nombre": estado.nombre if estado else "",
        "total": venta.total or 0,
        "impuesto": venta.impuesto or 0,
        "descuento": venta.descuento or 0,
        "activo": bool(venta.activo),
        "usuario_id": venta.usuario_id,
        "fecha_registro": venta.fecha_registro,
        "detalles": detalles_response,
    }

def get_venta(db: Session, venta_id: int):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        return None
    return _build_response(db, venta)

def get_ventas(db: Session, skip: int = 0, limit: int = 100):
    ventas = db.query(Venta).order_by(Venta.id.desc()).offset(skip).limit(limit).all()
    return [_build_response(db, v) for v in ventas]

def create_venta(db: Session, venta: VentaCreate, usuario_id: int):
    _validate_foreign_keys(db, venta.cliente_id, venta.comprobante_id, venta.estado_id, venta.detalles)

    subtotal = sum(d.cantidad * d.precio for d in venta.detalles)
    total = subtotal + (subtotal * (venta.impuesto or 0) / 100) - (subtotal * (venta.descuento or 0) / 100)

    if getattr(venta, 'automatico', True):
        comprobante = db.query(Comprobante).filter(Comprobante.id == venta.comprobante_id).with_for_update().first()
        num_comprobante = venta.num_comprobante or str(comprobante.numero).zfill(8)
        comprobante.numero += 1
    else:
        num_comprobante = venta.num_comprobante or ''

    fecha = venta.fecha if isinstance(venta.fecha, datetime) else datetime.combine(venta.fecha, datetime.min.time())
    fecha = datetime.combine(fecha.date(), datetime.now().time())

    db_venta = Venta(
        fecha=fecha,
        cliente_id=venta.cliente_id,
        comprobante_id=venta.comprobante_id,
        num_comprobante=num_comprobante,
        estado_id=venta.estado_id,
        total=total,
        impuesto=venta.impuesto or 0,
        descuento=venta.descuento or 0,
        usuario_id=usuario_id,
        activo=1 if venta.estado_id == 3 else 0
    )
    db.add(db_venta)
    db.flush()

    for detalle in venta.detalles:
        db_detalle = VentaDetalle(
            venta_id=db_venta.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            precio=detalle.precio,
            utilidad=detalle.utilidad or 0
        )
        db.add(db_detalle)
        _update_stock(db, detalle.producto_id, detalle.cantidad, sumar=False)

    db.commit()
    db.refresh(db_venta)
    return _build_response(db, db_venta)

def update_venta(db: Session, venta_id: int, venta: VentaUpdate):
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not db_venta:
        return None

    cliente_id = venta.cliente_id if venta.cliente_id is not None else db_venta.cliente_id
    comprobante_id = venta.comprobante_id if venta.comprobante_id is not None else db_venta.comprobante_id
    estado_id = venta.estado_id if venta.estado_id is not None else db_venta.estado_id
    detalles_data = venta.detalles if venta.detalles is not None else None

    if detalles_data is not None:
        _validate_foreign_keys(db, cliente_id, comprobante_id, estado_id, detalles_data)

    if venta.fecha is not None:
        db_venta.fecha = venta.fecha
    if venta.cliente_id is not None:
        db_venta.cliente_id = venta.cliente_id
    if venta.comprobante_id is not None:
        db_venta.comprobante_id = venta.comprobante_id
    if venta.num_comprobante is not None:
        db_venta.num_comprobante = venta.num_comprobante
    if venta.estado_id is not None:
        db_venta.estado_id = venta.estado_id
        db_venta.activo = 1 if venta.estado_id == 3 else 0
    if venta.impuesto is not None:
        db_venta.impuesto = venta.impuesto
    if venta.descuento is not None:
        db_venta.descuento = venta.descuento

    if detalles_data is not None:
        old_detalles = db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).all()
        for old_d in old_detalles:
            _update_stock(db, old_d.producto_id, old_d.cantidad, sumar=True)
        db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).delete()

        subtotal = sum(d.cantidad * d.precio for d in detalles_data)
        db_venta.total = subtotal + (subtotal * (db_venta.impuesto or 0) / 100) - (subtotal * (db_venta.descuento or 0) / 100)

        for detalle in detalles_data:
            db_detalle = VentaDetalle(
                venta_id=venta_id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                precio=detalle.precio,
                utilidad=detalle.utilidad or 0
            )
            db.add(db_detalle)
            _update_stock(db, detalle.producto_id, detalle.cantidad, sumar=False)
    else:
        subtotal = sum(d.cantidad * d.precio for d in db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).all())
        db_venta.total = subtotal + (subtotal * (db_venta.impuesto or 0) / 100) - (subtotal * (db_venta.descuento or 0) / 100)

    db.commit()
    db.refresh(db_venta)
    return _build_response(db, db_venta)

def _get_estado_anulado(db: Session):
    estado = db.query(Estado).filter(Estado.nombre == "ANULADO").first()
    if not estado:
        estado = Estado(nombre="ANULADO")
        db.add(estado)
        db.flush()
    return estado

def anular_venta(db: Session, venta_id: int):
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not db_venta:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_venta.estado_id == estado_anulado.id:
        raise HTTPException(status_code=400, detail="La venta ya está anulada")

    detalles = db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).all()
    for d in detalles:
        _update_stock(db, d.producto_id, d.cantidad, sumar=True)

    db_venta.estado_id = estado_anulado.id
    db_venta.activo = 0
    db.commit()
    db.refresh(db_venta)
    return _build_response(db, db_venta)

def delete_venta(db: Session, venta_id: int):
    db_venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not db_venta:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_venta.estado_id != estado_anulado.id:
        raise HTTPException(status_code=400, detail="Solo se puede eliminar ventas anuladas")

    db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).delete()
    db.delete(db_venta)
    db.commit()
    return {"message": "Venta deleted"}
