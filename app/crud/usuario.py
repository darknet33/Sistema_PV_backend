from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.auth import get_password_hash
from app.utils import capitalizar

def get_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def get_usuario_by_username(db: Session, username: str):
    return db.query(Usuario).filter(Usuario.username == username).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Usuario).offset(skip).limit(limit).all()

def create_usuario(db: Session, usuario: UsuarioCreate):
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuario(
        username=usuario.username,
        password=hashed_password,
        nombres=capitalizar(usuario.nombres),
        apellidos=capitalizar(usuario.apellidos),
        cargo=capitalizar(usuario.cargo),
        rol_id=usuario.rol_id
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def update_usuario(db: Session, usuario_id: int, usuario: UsuarioUpdate):
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        if usuario.username is not None:
            db_usuario.username = usuario.username
        if usuario.password:
            db_usuario.password = get_password_hash(usuario.password)
        if usuario.nombres is not None:
            db_usuario.nombres = capitalizar(usuario.nombres)
        if usuario.apellidos is not None:
            db_usuario.apellidos = capitalizar(usuario.apellidos)
        if usuario.cargo is not None:
            db_usuario.cargo = capitalizar(usuario.cargo)
        if usuario.rol_id is not None:
            db_usuario.rol_id = usuario.rol_id
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def change_password(db: Session, usuario_id: int, new_password: str):
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        db_usuario.password = get_password_hash(new_password)
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int):
    db_usuario = get_usuario(db, usuario_id)
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
    return db_usuario
