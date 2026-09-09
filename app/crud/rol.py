from sqlalchemy.orm import Session
from app.models.rol import Rol
from app.models.modulo import Modulo
from app.models.rol_modulo import RolModulo
from app.schemas.rol import RolCreate
from app.utils import capitalizar

def get_rol(db: Session, rol_id: int):
    return db.query(Rol).filter(Rol.id == rol_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Rol).offset(skip).limit(limit).all()

def create_rol(db: Session, rol: RolCreate):
    db_rol = Rol(nombre=capitalizar(rol.nombre))
    db.add(db_rol)
    db.flush()

    modulo_dashboard = db.query(Modulo).filter(Modulo.nombre.ilike("dashboard")).first()
    if modulo_dashboard:
        existe = db.query(RolModulo).filter(
            RolModulo.rol_id == db_rol.id,
            RolModulo.modulo_id == modulo_dashboard.id,
        ).first()
        if not existe:
            db.add(RolModulo(rol_id=db_rol.id, modulo_id=modulo_dashboard.id))

    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, rol_id: int, rol: RolCreate):
    db_rol = get_rol(db, rol_id)
    if db_rol:
        db_rol.nombre = capitalizar(rol.nombre)
        db.commit()
        db.refresh(db_rol)
    return db_rol

def delete_rol(db: Session, rol_id: int):
    db_rol = get_rol(db, rol_id)
    if db_rol:
        db.delete(db_rol)
        db.commit()
    return db_rol
