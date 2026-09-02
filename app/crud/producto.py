from typing import List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.producto import Producto
from app.models.compra_detalle import CompraDetalle
from app.models.venta_detalle import VentaDetalle
from app.models.cotizacion_detalle import CotizacionDetalle
from app.schemas.producto import ProductoCreate, ProductoUpdate
from app.crud.producto_unidad import (
    set_unidades_producto, get_unidades_producto, build_unidad_response, build_unidad_principal
)


def get_producto(db: Session, producto_id: int):
    return db.query(Producto).options(joinedload(Producto.usuario)).filter(Producto.id == producto_id).first()


def get_producto_full(db: Session, producto_id: int):
    prod = get_producto(db, producto_id)
    if not prod:
        return None
    return _build_full_response(db, prod)


def get_productos(db: Session, skip: int = 0, limit: int = 10000):
    return db.query(Producto).options(joinedload(Producto.usuario)).offset(skip).limit(limit).all()


def get_productos_full(db: Session, skip: int = 0, limit: int = 10000):
    prods = get_productos(db, skip, limit)
    return [_build_full_response(db, p) for p in prods]


def get_producto_by_codigo(db: Session, codigo: str):
    return db.query(Producto).options(joinedload(Producto.usuario)).filter(Producto.codigo == codigo).first()


def _attach_unidades(db: Session, prod: Producto) -> dict:
    unidades = get_unidades_producto(db, prod.id)
    return [build_unidad_response(u) for u in unidades]


def _attach_unidad_principal(db: Session, prod: Producto):
    return build_unidad_principal(prod.id, db)


def _build_full_response(db: Session, prod: Producto):
    unidades = _attach_unidades(db, prod)
    up = _attach_unidad_principal(db, prod)
    return {
        "id": prod.id,
        "codigo": prod.codigo,
        "categoria_id": prod.categoria_id,
        "descripcion": prod.descripcion,
        "marca": prod.marca,
        "procedencia": prod.procedencia,
        "precio": prod.precio,
        "utilidad": prod.utilidad,
        "stock_inicial": prod.stock_inicial,
        "stock_actual": prod.stock_actual,
        "stock_minimo": prod.stock_minimo,
        "stock_maximo": prod.stock_maximo,
        "imagen": prod.imagen,
        "usuario_id": prod.usuario_id,
        "activo": bool(prod.activo),
        "fecha_registro": prod.fecha_registro,
        "fecha_actualizado": prod.fecha_actualizado,
        "usuario_nombre": prod.usuario_nombre if hasattr(prod, "usuario_nombre") else (prod.usuario.username if prod.usuario else ""),
        "unidades": unidades,
        "unidad_principal": up,
    }


def create_producto(db: Session, producto: ProductoCreate, usuario_id: int = None):
    db_producto = Producto(
        codigo=producto.codigo,
        categoria_id=producto.categoria_id,
        descripcion=producto.descripcion,
        marca=producto.marca,
        procedencia=producto.procedencia,
        precio=producto.precio,
        utilidad=producto.utilidad,
        stock_inicial=producto.stock_inicial,
        stock_actual=producto.stock_actual,
        stock_minimo=producto.stock_minimo,
        stock_maximo=producto.stock_maximo,
        imagen=producto.imagen,
        usuario_id=usuario_id if usuario_id is not None else producto.usuario_id,
    )
    db.add(db_producto)
    db.flush()

    if producto.unidades:
        set_unidades_producto(db, db_producto.id, producto.unidades)

    db.commit()
    db.refresh(db_producto)
    return _build_full_response(db, db_producto)


def update_producto(db: Session, producto_id: int, producto: ProductoUpdate):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    for key, value in producto.model_dump(exclude_unset=True, exclude={"unidades"}).items():
        setattr(db_producto, key, value)
    if producto.unidades is not None:
        set_unidades_producto(db, db_producto.id, producto.unidades)
    db.commit()
    db.refresh(db_producto)
    return _build_full_response(db, db_producto)


def _tiene_relaciones(db: Session, producto_id: int) -> bool:
    en_compras = db.query(CompraDetalle).filter(CompraDetalle.producto_id == producto_id).first()
    en_ventas = db.query(VentaDetalle).filter(VentaDetalle.producto_id == producto_id).first()
    en_cotizaciones = db.query(CotizacionDetalle).filter(CotizacionDetalle.producto_id == producto_id).first()
    return bool(en_compras or en_ventas or en_cotizaciones)


def delete_producto(db: Session, producto_id: int):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    if _tiene_relaciones(db, producto_id):
        db_producto.activo = False
        db.commit()
        db.refresh(db_producto)
        return _build_full_response(db, db_producto)
    db.delete(db_producto)
    db.commit()
    return db_producto


def delete_productos_batch(db: Session, ids: List[int]):
    productos = db.query(Producto).filter(Producto.id.in_(ids)).all()
    count = 0
    for p in productos:
        if _tiene_relaciones(db, p.id):
            p.activo = False
        else:
            db.delete(p)
        count += 1
    db.commit()
    return count


def delete_all_productos(db: Session):
    ids_con_relaciones = set(
        row[0] for row in db.query(CompraDetalle.producto_id).distinct().all()
    ) | set(
        row[0] for row in db.query(VentaDetalle.producto_id).distinct().all()
    )
    productos = db.query(Producto).all()
    count = 0
    for p in productos:
        if p.id in ids_con_relaciones:
            p.activo = False
        else:
            db.delete(p)
        count += 1
    db.commit()
    return count
