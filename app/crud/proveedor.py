from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.proveedor import Proveedor
from app.models.compra import Compra
from app.schemas.proveedor import ProveedorCreate

def get_proveedor(db: Session, proveedor_id: int):
    return db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()

def get_proveedores(db: Session, skip: int = 0, limit: int = 100, solo_activos: bool = False):
    query = db.query(Proveedor)
    if solo_activos:
        query = query.filter(Proveedor.activo == True)
    return query.offset(skip).limit(limit).all()

def create_proveedor(db: Session, proveedor: ProveedorCreate):
    db_proveedor = Proveedor(
        nombre=proveedor.nombre,
        nit=proveedor.nit,
        materiales=proveedor.materiales,
        contacto=proveedor.contacto,
        celular_contacto=proveedor.celular_contacto,
        email_contacto=proveedor.email_contacto
    )
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor

def update_proveedor(db: Session, proveedor_id: int, proveedor: ProveedorCreate):
    db_proveedor = get_proveedor(db, proveedor_id)
    if db_proveedor:
        db_proveedor.nombre = proveedor.nombre
        db_proveedor.nit = proveedor.nit
        db_proveedor.materiales = proveedor.materiales
        db_proveedor.contacto = proveedor.contacto
        db_proveedor.celular_contacto = proveedor.celular_contacto
        db_proveedor.email_contacto = proveedor.email_contacto
        db.commit()
        db.refresh(db_proveedor)
    return db_proveedor

def delete_proveedor(db: Session, proveedor_id: int):
    db_proveedor = get_proveedor(db, proveedor_id)
    if not db_proveedor:
        return None
    tiene_compras = db.query(Compra).filter(Compra.proveedor_id == proveedor_id).first()
    if tiene_compras:
        db_proveedor.activo = False
        db.commit()
        db.refresh(db_proveedor)
        return db_proveedor
    db.delete(db_proveedor)
    db.commit()
    return db_proveedor
