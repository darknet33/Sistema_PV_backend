from sqlalchemy.orm import Session
from app.models.rol_modulo import RolModulo

def create_rol_modulo(db: Session, rol_id: int, modulo_id: int):
    db_rol_modulo = RolModulo(rol_id=rol_id, modulo_id=modulo_id)
    db.add(db_rol_modulo)
    db.commit()
    db.refresh(db_rol_modulo)
    return db_rol_modulo

def delete_rol_modulo(db: Session, rol_id: int, modulo_id: int):
    db_rol_modulo = db.query(RolModulo).filter(
        RolModulo.rol_id == rol_id,
        RolModulo.modulo_id == modulo_id
    ).first()
    if db_rol_modulo:
        db.delete(db_rol_modulo)
        db.commit()
    return db_rol_modulo

def get_modulos_by_rol(db: Session, rol_id: int):
    return db.query(RolModulo).filter(RolModulo.rol_id == rol_id).all()

def get_roles_by_modulo(db: Session, modulo_id: int):
    return db.query(RolModulo).filter(RolModulo.modulo_id == modulo_id).all()
