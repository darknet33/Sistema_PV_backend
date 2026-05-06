from sqlalchemy.orm import Session
from app.models.estado import Estado
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
    if db_estado:
        db.delete(db_estado)
        db.commit()
    return db_estado
