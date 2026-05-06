from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.modulo import ModuloCreate, ModuloResponse
from app.crud.modulo import get_modulos, get_modulo, create_modulo, update_modulo, delete_modulo

router = APIRouter()

@router.get("/", response_model=List[ModuloResponse])
def read_modulos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_modulos(db, skip, limit)

@router.get("/{modulo_id}", response_model=ModuloResponse)
def read_modulo(modulo_id: int, db: Session = Depends(get_db)):
    db_modulo = get_modulo(db, modulo_id)
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Modulo not found")
    return db_modulo

@router.post("/", response_model=ModuloResponse)
def create_modulo_endpoint(modulo: ModuloCreate, db: Session = Depends(get_db)):
    return create_modulo(db, modulo)

@router.put("/{modulo_id}", response_model=ModuloResponse)
def update_modulo_endpoint(modulo_id: int, modulo: ModuloCreate, db: Session = Depends(get_db)):
    db_modulo = update_modulo(db, modulo_id, modulo)
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Modulo not found")
    return db_modulo

@router.delete("/{modulo_id}")
def delete_modulo_endpoint(modulo_id: int, db: Session = Depends(get_db)):
    db_modulo = delete_modulo(db, modulo_id)
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Modulo not found")
    return {"message": "Modulo deleted"}
