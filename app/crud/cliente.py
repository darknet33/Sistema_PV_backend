from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.cliente import Cliente
from app.models.venta import Venta
from app.models.cotizacion import Cotizacion
from app.schemas.cliente import ClienteCreate
from app.utils import capitalizar

def get_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Cliente).offset(skip).limit(limit).all()

def create_cliente(db: Session, cliente: ClienteCreate):
    db_cliente = Cliente(
        nombre=capitalizar(cliente.nombre),
        nit=cliente.nit,
        celular=cliente.celular,
        direccion=capitalizar(cliente.direccion)
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def update_cliente(db: Session, cliente_id: int, cliente: ClienteCreate):
    db_cliente = get_cliente(db, cliente_id)
    if db_cliente:
        db_cliente.nombre = capitalizar(cliente.nombre)
        db_cliente.nit = cliente.nit
        db_cliente.celular = cliente.celular
        db_cliente.direccion = capitalizar(cliente.direccion)
        db.commit()
        db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db: Session, cliente_id: int):
    db_cliente = get_cliente(db, cliente_id)
    if db_cliente:
        en_ventas = db.query(Venta).filter(Venta.cliente_id == cliente_id).first()
        en_cotizaciones = db.query(Cotizacion).filter(Cotizacion.cliente_id == cliente_id).first()
        if en_ventas or en_cotizaciones:
            raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene ventas o cotizaciones asociadas")
        db.delete(db_cliente)
        db.commit()
    return db_cliente
