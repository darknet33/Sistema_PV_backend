from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.producto_unidad import ProductoUnidad
from app.models.unidad_medida import UnidadMedida
from app.schemas.producto_unidad import ProductoUnidadCreate


def get_unidades_producto(db: Session, producto_id: int) -> List[ProductoUnidad]:
    return db.query(ProductoUnidad).filter(ProductoUnidad.producto_id == producto_id).all()


def set_unidades_producto(db: Session, producto_id: int, unidades: List[ProductoUnidadCreate]):
    db.query(ProductoUnidad).filter(ProductoUnidad.producto_id == producto_id).delete()
    for u in unidades:
        db_obj = ProductoUnidad(
            producto_id=producto_id,
            unidad_id=u.unidad_id,
            es_principal=u.es_principal,
            factor_conversion=u.factor_conversion or Decimal("1"),
        )
        db.add(db_obj)
    db.flush()


def get_unidad_principal(db: Session, producto_id: int) -> Optional[ProductoUnidad]:
    return (
        db.query(ProductoUnidad)
        .filter(ProductoUnidad.producto_id == producto_id, ProductoUnidad.es_principal == True)
        .first()
    )


def get_factor_conversion(db: Session, producto_id: int, unidad_id: int) -> Decimal:
    pu = (
        db.query(ProductoUnidad)
        .filter(ProductoUnidad.producto_id == producto_id, ProductoUnidad.unidad_id == unidad_id)
        .first()
    )
    return pu.factor_conversion if pu else Decimal("1")


def build_unidad_response(pu: ProductoUnidad) -> dict:
    uname = ""
    uabrev = ""
    if pu.unidad:
        uname = pu.unidad.nombre or ""
        uabrev = pu.unidad.abreviatura or ""
    return {
        "id": pu.id,
        "unidad_id": pu.unidad_id,
        "unidad_nombre": uname,
        "unidad_abreviatura": uabrev,
        "es_principal": bool(pu.es_principal),
        "factor_conversion": pu.factor_conversion or Decimal("1"),
    }


def build_unidad_principal(producto_id: int, db: Session) -> Optional[dict]:
    pu = get_unidad_principal(db, producto_id)
    if pu:
        return build_unidad_response(pu)
    return None
