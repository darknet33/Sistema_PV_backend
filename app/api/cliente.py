from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.crud.cliente import get_clientes, get_cliente, create_cliente, update_cliente, delete_cliente

router = APIRouter()

@router.get("/", response_model=List[ClienteResponse])
def read_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_clientes(db, skip, limit)

@router.get("/{cliente_id}", response_model=ClienteResponse)
def read_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return db_cliente

@router.post("/", response_model=ClienteResponse)
def create_cliente_endpoint(cliente: ClienteCreate, db: Session = Depends(get_db)):
    return create_cliente(db, cliente)

@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente_endpoint(cliente_id: int, cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = update_cliente(db, cliente_id, cliente)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return db_cliente

@router.delete("/{cliente_id}")
def delete_cliente_endpoint(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = delete_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return {"message": "Cliente deleted"}

@router.patch("/{cliente_id}/toggle-activo", response_model=ClienteResponse)
def toggle_cliente_activo(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    db_cliente.activo = not db_cliente.activo
    db.commit()
    db.refresh(db_cliente)
    return db_cliente
