from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException
from datetime import datetime, date
from app.models.compra import Compra
from app.models.compra_detalle import CompraDetalle
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from app.models.comprobante import Comprobante
from app.models.estado import Estado
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.schemas.compra import CompraCreate, CompraUpdate

def _validate_foreign_keys(db: Session, proveedor_id: int, comprobante_id: int, estado_id: int, detalles: list):
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=400, detail=f"Proveedor {proveedor_id} no existe")

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
            producto.stock_actual = (producto.stock_actual or 0) - cantidad

def _build_response(db: Session, compra: Compra):
    proveedor = db.query(Proveedor).filter(Proveedor.id == compra.proveedor_id).first()
    comprobante = db.query(Comprobante).filter(Comprobante.id == compra.comprobante_id).first()
    estado = db.query(Estado).filter(Estado.id == compra.estado_id).first()
    detalles = db.query(CompraDetalle).options(
        selectinload(CompraDetalle.producto).selectinload(Producto.categoria)
    ).filter(CompraDetalle.compra_id == compra.id).all()

    detalles_response = []
    for d in detalles:
        prod = d.producto
        cat_nombre = ""
        if prod and prod.categoria:
            cat_nombre = prod.categoria.nombre
        detalles_response.append({
            "id": d.id,
            "producto_id": d.producto_id,
            "producto_nombre": prod.descripcion if prod else "",
            "producto_codigo": prod.codigo if prod else "",
            "producto_categoria": cat_nombre,
            "cantidad": d.cantidad,
            "costo": d.costo,
        })

    usuario = db.query(Usuario).filter(Usuario.id == compra.usuario_id).first()

    return {
        "id": compra.id,
        "fecha": compra.fecha,
        "proveedor_id": compra.proveedor_id,
        "proveedor_nombre": proveedor.nombre if proveedor else "",
        "comprobante_id": compra.comprobante_id,
        "comprobante_nombre": comprobante.nombre if comprobante else "",
        "num_comprobante": compra.num_comprobante,
        "estado_id": compra.estado_id,
        "estado_nombre": estado.nombre if estado else "",
        "total": compra.total or 0,
        "activo": bool(compra.activo),
        "usuario_id": compra.usuario_id,
        "usuario_username": usuario.username if usuario else "",
        "fecha_registro": compra.fecha_registro,
        "detalles": detalles_response,
    }

def get_compra(db: Session, compra_id: int):
    compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not compra:
        return None
    return _build_response(db, compra)

def get_compras(db: Session, skip: int = 0, limit: int = 100):
    compras = db.query(Compra).order_by(Compra.id.desc()).offset(skip).limit(limit).all()
    return [_build_response(db, c) for c in compras]

def create_compra(db: Session, compra: CompraCreate, usuario_id: int):
    _validate_foreign_keys(db, compra.proveedor_id, compra.comprobante_id, compra.estado_id, compra.detalles)

    total = sum(detalle.cantidad * detalle.costo for detalle in compra.detalles)

    if getattr(compra, 'automatico', True):
        comprobante = db.query(Comprobante).filter(Comprobante.id == compra.comprobante_id).with_for_update().first()
        num_comprobante = compra.num_comprobante or str(comprobante.numero).zfill(8)
        comprobante.numero += 1
    else:
        num_comprobante = compra.num_comprobante or ''

    fecha = compra.fecha if isinstance(compra.fecha, datetime) else datetime.combine(compra.fecha, datetime.min.time())
    fecha = datetime.combine(fecha.date(), datetime.now().time())

    db_compra = Compra(
        fecha=fecha,
        proveedor_id=compra.proveedor_id,
        comprobante_id=compra.comprobante_id,
        num_comprobante=num_comprobante,
        estado_id=compra.estado_id,
        total=total,
        usuario_id=usuario_id,
        activo=1 if compra.estado_id == 3 else 0
    )
    db.add(db_compra)
    db.flush()

    for detalle in compra.detalles:
        db_detalle = CompraDetalle(
            compra_id=db_compra.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            costo=detalle.costo
        )
        db.add(db_detalle)
        _update_stock(db, detalle.producto_id, detalle.cantidad, sumar=True)

    db.commit()
    db.refresh(db_compra)
    return _build_response(db, db_compra)

def update_compra(db: Session, compra_id: int, compra: CompraUpdate):
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not db_compra:
        return None

    proveedor_id = compra.proveedor_id if compra.proveedor_id is not None else db_compra.proveedor_id
    comprobante_id = compra.comprobante_id if compra.comprobante_id is not None else db_compra.comprobante_id
    estado_id = compra.estado_id if compra.estado_id is not None else db_compra.estado_id
    detalles_data = compra.detalles if compra.detalles is not None else None

    if detalles_data is not None:
        _validate_foreign_keys(db, proveedor_id, comprobante_id, estado_id, detalles_data)

    if compra.fecha is not None:
        db_compra.fecha = compra.fecha
    if compra.proveedor_id is not None:
        db_compra.proveedor_id = compra.proveedor_id
    if compra.comprobante_id is not None:
        db_compra.comprobante_id = compra.comprobante_id
    if compra.num_comprobante is not None:
        db_compra.num_comprobante = compra.num_comprobante
    if compra.estado_id is not None:
        db_compra.estado_id = compra.estado_id
        db_compra.activo = 1 if compra.estado_id == 3 else 0

    if detalles_data is not None:
        old_detalles = db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).all()
        for old_d in old_detalles:
            _update_stock(db, old_d.producto_id, old_d.cantidad, sumar=False)
        db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).delete()

        total = sum(d.cantidad * d.costo for d in detalles_data)
        db_compra.total = total

        for detalle in detalles_data:
            db_detalle = CompraDetalle(
                compra_id=compra_id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                costo=detalle.costo
            )
            db.add(db_detalle)
            _update_stock(db, detalle.producto_id, detalle.cantidad, sumar=True)

    db.commit()
    db.refresh(db_compra)
    return _build_response(db, db_compra)

def _get_estado_anulado(db: Session):
    estado = db.query(Estado).filter(Estado.nombre == "Anulado").first()
    if not estado:
        estado = Estado(nombre="Anulado")
        db.add(estado)
        db.flush()
    return estado

def _validar_stock_para_anular_compra(db: Session, detalles: list):
    for d in detalles:
        producto = db.query(Producto).filter(Producto.id == d.producto_id).first()
        if not producto:
            raise HTTPException(status_code=400, detail=f"Producto {d.producto_id} no existe")
        stock = (producto.stock_actual or 0)
        if stock - d.cantidad < 0:
            nombre = producto.descripcion or producto.codigo
            raise HTTPException(
                status_code=400,
                detail=f"No se puede anular la compra: stock insuficiente para '{nombre}'"
            )

def anular_compra(db: Session, compra_id: int):
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not db_compra:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_compra.estado_id == estado_anulado.id:
        raise HTTPException(status_code=400, detail="La compra ya está anulada")

    detalles = db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).all()
    _validar_stock_para_anular_compra(db, detalles)
    for d in detalles:
        _update_stock(db, d.producto_id, d.cantidad, sumar=False)

    db_compra.estado_id = estado_anulado.id
    db_compra.activo = 0
    db.commit()
    db.refresh(db_compra)
    return _build_response(db, db_compra)

def delete_compra(db: Session, compra_id: int):
    db_compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not db_compra:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_compra.estado_id != estado_anulado.id:
        raise HTTPException(status_code=400, detail="Solo se puede eliminar compras anuladas")

    db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).delete()
    db.delete(db_compra)
    db.commit()
    return {"message": "Compra deleted"}
