from sqlalchemy.orm import Session
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.schemas.venta import VentaCreate
from datetime import datetime

def get_venta(db: Session, venta_id: int):
    return db.query(Venta).filter(Venta.id == venta_id).first()

def get_ventas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Venta).order_by(Venta.fecha.desc()).offset(skip).limit(limit).all()

def create_venta(db: Session, venta: VentaCreate, usuario_id: int):
    subtotal = sum(d.cantidad * d.precio for d in venta.detalles)
    total = subtotal + (subtotal * venta.impuesto / 100) - (subtotal * venta.descuento / 100)
    
    db_venta = Venta(
        fecha=venta.fecha,
        cliente_id=venta.cliente_id,
        comprobante_id=venta.comprobante_id,
        num_comprobante=venta.num_comprobante,
        estado_id=venta.estado_id,
        total=total,
        impuesto=venta.impuesto,
        descuento=venta.descuento,
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
            utilidad=detalle.utilidad
        )
        db.add(db_detalle)
    
    db.commit()
    db.refresh(db_venta)
    return db_venta

def update_venta(db: Session, venta_id: int, venta: VentaCreate):
    db_venta = get_venta(db, venta_id)
    if db_venta:
        db_venta.fecha = venta.fecha
        db_venta.cliente_id = venta.cliente_id
        db_venta.comprobante_id = venta.comprobante_id
        db_venta.num_comprobante = venta.num_comprobante
        db_venta.estado_id = venta.estado_id
        db_venta.impuesto = venta.impuesto
        db_venta.descuento = venta.descuento
        
        subtotal = sum(d.cantidad * d.precio for d in venta.detalles)
        db_venta.total = subtotal + (subtotal * venta.impuesto / 100) - (subtotal * venta.descuento / 100)
        
        db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).delete()
        
        for detalle in venta.detalles:
            db_detalle = VentaDetalle(
                venta_id=venta_id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                precio=detalle.precio,
                utilidad=detalle.utilidad
            )
            db.add(db_detalle)
        
        db.commit()
        db.refresh(db_venta)
    return db_venta

def delete_venta(db: Session, venta_id: int):
    db_venta = get_venta(db, venta_id)
    if db_venta:
        db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).delete()
        db.delete(db_venta)
        db.commit()
    return db_venta
