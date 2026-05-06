from sqlalchemy.orm import Session
from app.models.compra import Compra
from app.models.compra_detalle import CompraDetalle
from app.schemas.compra import CompraCreate
from datetime import datetime

def get_compra(db: Session, compra_id: int):
    return db.query(Compra).filter(Compra.id == compra_id).first()

def get_compras(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Compra).order_by(Compra.fecha.desc()).offset(skip).limit(limit).all()

def create_compra(db: Session, compra: CompraCreate, usuario_id: int):
    total = sum(detalle.cantidad * detalle.costo for detalle in compra.detalles)
    
    db_compra = Compra(
        fecha=compra.fecha,
        proveedor_id=compra.proveedor_id,
        comprobante_id=compra.comprobante_id,
        num_comprobante=compra.num_comprobante,
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
    
    db.commit()
    db.refresh(db_compra)
    return db_compra

def update_compra(db: Session, compra_id: int, compra: CompraCreate):
    db_compra = get_compra(db, compra_id)
    if db_compra:
        db_compra.fecha = compra.fecha
        db_compra.proveedor_id = compra.proveedor_id
        db_compra.comprobante_id = compra.comprobante_id
        db_compra.num_comprobante = compra.num_comprobante
        db_compra.estado_id = compra.estado_id
        db_compra.total = sum(d.cantidad * d.costo for d in compra.detalles)
        
        db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).delete()
        
        for detalle in compra.detalles:
            db_detalle = CompraDetalle(
                compra_id=compra_id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                costo=detalle.costo
            )
            db.add(db_detalle)
        
        db.commit()
        db.refresh(db_compra)
    return db_compra

def delete_compra(db: Session, compra_id: int):
    db_compra = get_compra(db, compra_id)
    if db_compra:
        db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).delete()
        db.delete(db_compra)
        db.commit()
    return db_compra
