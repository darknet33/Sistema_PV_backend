from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.estado import Estado
from app.models.compra import Compra
from app.models.venta import Venta
from app.schemas.estado import EstadoCreate

def get_estado(db: Session, estado_id: int):
    return db.query(Estado).filter(Estado.id == estado_id).first()

def get_estados(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Estado).offset(skip).limit(limit).all()

def create_estado(db: Session, estado: EstadoCreate):
    db_estado = Estado(nombre=estado.nombre)
    db.add(db_estado)
    db.commit()
    db.refresh(db_estado)
    return db_estado

def update_estado(db: Session, estado_id: int, estado: EstadoCreate):
    db_estado = get_estado(db, estado_id)
    if db_estado:
        db_estado.nombre = estado.nombre
        db.commit()
        db.refresh(db_estado)
    return db_estado

def delete_estado(db: Session, estado_id: int):
    db_estado = get_estado(db, estado_id)
    if not db_estado:
        return None
    en_compras = db.query(Compra).filter(Compra.estado_id == estado_id).first()
    en_ventas = db.query(Venta).filter(Venta.estado_id == estado_id).first()
    if en_compras or en_ventas:
        raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene compras o ventas asociadas")
    db.delete(db_estado)
    db.commit()
    return db_estado
