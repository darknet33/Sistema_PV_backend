from sqlalchemy.orm import Session
from app.models.rol import Rol
from app.schemas.rol import RolCreate

def get_rol(db: Session, rol_id: int):
    return db.query(Rol).filter(Rol.id == rol_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Rol).offset(skip).limit(limit).all()

def create_rol(db: Session, rol: RolCreate):
    db_rol = Rol(nombre=rol.nombre)
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, rol_id: int, rol: RolCreate):
    db_rol = get_rol(db, rol_id)
    if db_rol:
        db_rol.nombre = rol.nombre
        db.commit()
        db.refresh(db_rol)
    return db_rol

def delete_rol(db: Session, rol_id: int):
    db_rol = get_rol(db, rol_id)
    if db_rol:
        db.delete(db_rol)
        db.commit()
    return db_rol
