from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.estado import EstadoCreate, EstadoResponse
from app.crud.estado import get_estados, get_estado, create_estado, update_estado, delete_estado

router = APIRouter()

@router.get("/", response_model=List[EstadoResponse])
def read_estados(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_estados(db, skip, limit)

@router.get("/{estado_id}", response_model=EstadoResponse)
def read_estado(estado_id: int, db: Session = Depends(get_db)):
    db_estado = get_estado(db, estado_id)
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado not found")
    return db_estado

@router.post("/", response_model=EstadoResponse)
def create_estado_endpoint(estado: EstadoCreate, db: Session = Depends(get_db)):
    return create_estado(db, estado)

@router.put("/{estado_id}", response_model=EstadoResponse)
def update_estado_endpoint(estado_id: int, estado: EstadoCreate, db: Session = Depends(get_db)):
    db_estado = update_estado(db, estado_id, estado)
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado not found")
    return db_estado

@router.delete("/{estado_id}")
def delete_estado_endpoint(estado_id: int, db: Session = Depends(get_db)):
    db_estado = delete_estado(db, estado_id)
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado not found")
    return {"message": "Estado deleted"}
