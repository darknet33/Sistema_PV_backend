from sqlalchemy.orm import Session
from app.models.modulo import Modulo
from app.schemas.modulo import ModuloCreate

def get_modulo(db: Session, modulo_id: int):
    return db.query(Modulo).filter(Modulo.id == modulo_id).first()

def get_modulos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Modulo).offset(skip).limit(limit).all()

def create_modulo(db: Session, modulo: ModuloCreate):
    db_modulo = Modulo(nombre=modulo.nombre, activo=modulo.activo)
    db.add(db_modulo)
    db.commit()
    db.refresh(db_modulo)
    return db_modulo

def update_modulo(db: Session, modulo_id: int, modulo: ModuloCreate):
    db_modulo = get_modulo(db, modulo_id)
    if db_modulo:
        db_modulo.nombre = modulo.nombre
        db_modulo.activo = modulo.activo
        db.commit()
        db.refresh(db_modulo)
    return db_modulo

def delete_modulo(db: Session, modulo_id: int):
    db_modulo = get_modulo(db, modulo_id)
    if db_modulo:
        db.delete(db_modulo)
        db.commit()
    return db_modulo
