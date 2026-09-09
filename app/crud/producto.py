from typing import List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.producto import Producto
from app.models.compra_detalle import CompraDetalle
from app.models.venta_detalle import VentaDetalle
from app.models.cotizacion_detalle import CotizacionDetalle
from app.models.nota_entrega import NotaEntregaDetalle
from app.schemas.producto import ProductoCreate, ProductoUpdate
from app.utils import capitalizar
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
    ids_en_uso = _ids_en_uso(db)
    return [_build_full_response(db, p, p.id in ids_en_uso) for p in prods]


def get_producto_by_codigo(db: Session, codigo: str):
    return db.query(Producto).options(joinedload(Producto.usuario)).filter(Producto.codigo == codigo).first()


def _attach_unidades(db: Session, prod: Producto) -> dict:
    unidades = get_unidades_producto(db, prod.id)
    return [build_unidad_response(u) for u in unidades]


def _attach_unidad_principal(db: Session, prod: Producto):
    return build_unidad_principal(prod.id, db)


def _build_full_response(db: Session, prod: Producto, en_uso: bool = None):
    if en_uso is None:
        en_uso = _tiene_relaciones(db, prod.id)
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
        "en_uso": bool(en_uso),
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
        descripcion=capitalizar(producto.descripcion),
        marca=capitalizar(producto.marca),
        procedencia=capitalizar(producto.procedencia),
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
    if "descripcion" in producto.model_fields_set and producto.descripcion is not None:
        db_producto.descripcion = capitalizar(producto.descripcion)
    if "marca" in producto.model_fields_set and producto.marca is not None:
        db_producto.marca = capitalizar(producto.marca)
    if "procedencia" in producto.model_fields_set and producto.procedencia is not None:
        db_producto.procedencia = capitalizar(producto.procedencia)
    if producto.unidades is not None:
        set_unidades_producto(db, db_producto.id, producto.unidades)
    db.commit()
    db.refresh(db_producto)
    return _build_full_response(db, db_producto)


def _ids_en_uso(db: Session) -> set:
    ids = set()
    for table in (CompraDetalle, VentaDetalle, CotizacionDetalle, NotaEntregaDetalle):
        ids.update(row[0] for row in db.query(table.producto_id).distinct().all())
    return ids


def _tiene_relaciones(db: Session, producto_id: int) -> bool:
    return producto_id in _ids_en_uso(db)


def delete_producto(db: Session, producto_id: int):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    en_uso = _tiene_relaciones(db, producto_id)
    if en_uso:
        db_producto.activo = False
        db.commit()
        db.refresh(db_producto)
    else:
        db.delete(db_producto)
        db.commit()
    return {"id": producto_id, "en_uso": en_uso, "soft_deleted": en_uso}


def delete_productos_batch(db: Session, ids: List[int]):
    productos = db.query(Producto).filter(Producto.id.in_(ids)).all()
    ids_en_uso = _ids_en_uso(db)
    soft_deleted = 0
    for p in productos:
        if p.id in ids_en_uso:
            p.activo = False
            soft_deleted += 1
        else:
            db.delete(p)
    db.commit()
    return {"count": len(productos), "soft_deleted": soft_deleted, "hard_deleted": len(productos) - soft_deleted}


def delete_all_productos(db: Session):
    ids_en_uso = _ids_en_uso(db)
    productos = db.query(Producto).all()
    soft_deleted = 0
    for p in productos:
        if p.id in ids_en_uso:
            p.activo = False
            soft_deleted += 1
        else:
            db.delete(p)
    db.commit()
    return {"count": len(productos), "soft_deleted": soft_deleted, "hard_deleted": len(productos) - soft_deleted}
