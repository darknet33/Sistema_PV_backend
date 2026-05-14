from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.producto import Producto
from app.models.compra_detalle import CompraDetalle
from app.models.venta_detalle import VentaDetalle
from app.schemas.producto import ProductoCreate, ProductoUpdate

def get_producto(db: Session, producto_id: int):
    return db.query(Producto).options(joinedload(Producto.usuario)).filter(Producto.id == producto_id).first()

def get_productos(db: Session, skip: int = 0, limit: int = 10000):
    return db.query(Producto).options(joinedload(Producto.usuario)).offset(skip).limit(limit).all()

def get_producto_by_codigo(db: Session, codigo: str):
    return db.query(Producto).options(joinedload(Producto.usuario)).filter(Producto.codigo == codigo).first()

def create_producto(db: Session, producto: ProductoCreate):
    db_producto = Producto(
        codigo=producto.codigo,
        categoria_id=producto.categoria_id,
        descripcion=producto.descripcion,
        marca=producto.marca,
        precio=producto.precio,
        utilidad=producto.utilidad,
        peso=producto.peso,
        stock_inicial=producto.stock_inicial,
        stock_actual=producto.stock_actual,
        stock_minimo=producto.stock_minimo,
        usuario_id=producto.usuario_id
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def update_producto(db: Session, producto_id: int, producto: ProductoUpdate):
    db_producto = get_producto(db, producto_id)
    if db_producto:
        for key, value in producto.model_dump(exclude_unset=True).items():
            setattr(db_producto, key, value)
        db.commit()
        db.refresh(db_producto)
    return db_producto

def delete_producto(db: Session, producto_id: int):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        return None
    en_compras = db.query(CompraDetalle).filter(CompraDetalle.producto_id == producto_id).first()
    en_ventas = db.query(VentaDetalle).filter(VentaDetalle.producto_id == producto_id).first()
    if en_compras or en_ventas:
        db_producto.activo = False
        db.commit()
        db.refresh(db_producto)
        return db_producto
    db.delete(db_producto)
    db.commit()
    return db_producto
