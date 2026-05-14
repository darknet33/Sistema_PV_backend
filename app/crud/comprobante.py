from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.comprobante import Comprobante
from app.models.compra import Compra
from app.models.venta import Venta
from app.schemas.comprobante import ComprobanteCreate

def get_comprobante(db: Session, comprobante_id: int):
    return db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()

def get_comprobantes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Comprobante).offset(skip).limit(limit).all()

def create_comprobante(db: Session, comprobante: ComprobanteCreate):
    db_comprobante = Comprobante(nombre=comprobante.nombre, numero=comprobante.numero)
    db.add(db_comprobante)
    db.commit()
    db.refresh(db_comprobante)
    return db_comprobante

def update_comprobante(db: Session, comprobante_id: int, comprobante: ComprobanteCreate):
    db_comprobante = get_comprobante(db, comprobante_id)
    if db_comprobante:
        db_comprobante.nombre = comprobante.nombre
        db_comprobante.numero = comprobante.numero
        db.commit()
        db.refresh(db_comprobante)
    return db_comprobante

def delete_comprobante(db: Session, comprobante_id: int):
    db_comprobante = get_comprobante(db, comprobante_id)
    if not db_comprobante:
        return None
    en_compras = db.query(Compra).filter(Compra.comprobante_id == comprobante_id).first()
    en_ventas = db.query(Venta).filter(Venta.comprobante_id == comprobante_id).first()
    if en_compras or en_ventas:
        raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene compras o ventas asociadas")
    db.delete(db_comprobante)
    db.commit()
    return db_comprobante
