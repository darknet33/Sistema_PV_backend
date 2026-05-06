from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.compra import CompraCreate, CompraResponse
from app.crud.compra import get_compras, get_compra, create_compra, update_compra, delete_compra

router = APIRouter()

@router.get("/", response_model=List[CompraResponse])
def read_compras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_compras(db, skip, limit)

@router.get("/{compra_id}", response_model=CompraResponse)
def read_compra(compra_id: int, db: Session = Depends(get_db)):
    db_compra = get_compra(db, compra_id)
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra not found")
    return db_compra

@router.post("/", response_model=CompraResponse)
def create_compra_endpoint(compra: CompraCreate, db: Session = Depends(get_db)):
    return create_compra(db, compra, usuario_id=1)

@router.put("/{compra_id}", response_model=CompraResponse)
def update_compra_endpoint(compra_id: int, compra: CompraCreate, db: Session = Depends(get_db)):
    db_compra = update_compra(db, compra_id, compra)
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra not found")
    return db_compra

@router.delete("/{compra_id}")
def delete_compra_endpoint(compra_id: int, db: Session = Depends(get_db)):
    db_compra = delete_compra(db, compra_id)
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra not found")
    return {"message": "Compra deleted"}
