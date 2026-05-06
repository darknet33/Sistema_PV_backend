from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.venta import VentaCreate, VentaResponse
from app.crud.venta import get_ventas, get_venta, create_venta, update_venta, delete_venta

router = APIRouter()

@router.get("/", response_model=List[VentaResponse])
def read_ventas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_ventas(db, skip, limit)

@router.get("/{venta_id}", response_model=VentaResponse)
def read_venta(venta_id: int, db: Session = Depends(get_db)):
    db_venta = get_venta(db, venta_id)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    return db_venta

@router.post("/", response_model=VentaResponse)
def create_venta_endpoint(venta: VentaCreate, db: Session = Depends(get_db)):
    return create_venta(db, venta, usuario_id=1)

@router.put("/{venta_id}", response_model=VentaResponse)
def update_venta_endpoint(venta_id: int, venta: VentaCreate, db: Session = Depends(get_db)):
    db_venta = update_venta(db, venta_id, venta)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    return db_venta

@router.delete("/{venta_id}")
def delete_venta_endpoint(venta_id: int, db: Session = Depends(get_db)):
    db_venta = delete_venta(db, venta_id)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    return {"message": "Venta deleted"}
