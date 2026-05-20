from sqlalchemy.orm import Session
from app.models.cliente import Cliente
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
        direccion=cliente.direccion
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
        db_cliente.direccion = cliente.direccion
        db.commit()
        db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db: Session, cliente_id: int):
    db_cliente = get_cliente(db, cliente_id)
    if db_cliente:
        db.delete(db_cliente)
        db.commit()
    return db_cliente
