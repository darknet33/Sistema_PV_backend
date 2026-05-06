from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.comprobante import ComprobanteCreate, ComprobanteResponse
from app.crud.comprobante import get_comprobantes, get_comprobante, create_comprobante, update_comprobante, delete_comprobante

router = APIRouter()

@router.get("/", response_model=List[ComprobanteResponse])
def read_comprobantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_comprobantes(db, skip, limit)

@router.get("/{comprobante_id}", response_model=ComprobanteResponse)
def read_comprobante(comprobante_id: int, db: Session = Depends(get_db)):
    db_comprobante = get_comprobante(db, comprobante_id)
    if not db_comprobante:
        raise HTTPException(status_code=404, detail="Comprobante not found")
    return db_comprobante

@router.post("/", response_model=ComprobanteResponse)
def create_comprobante_endpoint(comprobante: ComprobanteCreate, db: Session = Depends(get_db)):
    return create_comprobante(db, comprobante)

@router.put("/{comprobante_id}", response_model=ComprobanteResponse)
def update_comprobante_endpoint(comprobante_id: int, comprobante: ComprobanteCreate, db: Session = Depends(get_db)):
    db_comprobante = update_comprobante(db, comprobante_id, comprobante)
    if not db_comprobante:
        raise HTTPException(status_code=404, detail="Comprobante not found")
    return db_comprobante

@router.delete("/{comprobante_id}")
def delete_comprobante_endpoint(comprobante_id: int, db: Session = Depends(get_db)):
    db_comprobante = delete_comprobante(db, comprobante_id)
    if not db_comprobante:
        raise HTTPException(status_code=404, detail="Comprobante not found")
    return {"message": "Comprobante deleted"}
