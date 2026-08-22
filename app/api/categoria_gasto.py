from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.categoria_gasto import CategoriaGastoCreate, CategoriaGastoResponse
from app.crud.categoria_gasto import get_categorias_gastos, get_categoria_gasto, create_categoria_gasto, update_categoria_gasto, delete_categoria_gasto

router = APIRouter()

@router.get("/", response_model=List[CategoriaGastoResponse])
def read_categorias_gastos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_categorias_gastos(db, skip, limit)

@router.get("/{categoria_id}", response_model=CategoriaGastoResponse)
def read_categoria_gasto(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria = get_categoria_gasto(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría de gasto not found")
    return db_categoria

@router.post("/", response_model=CategoriaGastoResponse)
def create_categoria_gasto_endpoint(categoria: CategoriaGastoCreate, db: Session = Depends(get_db)):
    return create_categoria_gasto(db, categoria)

@router.put("/{categoria_id}", response_model=CategoriaGastoResponse)
def update_categoria_gasto_endpoint(categoria_id: int, categoria: CategoriaGastoCreate, db: Session = Depends(get_db)):
    db_categoria = update_categoria_gasto(db, categoria_id, categoria)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría de gasto not found")
    return db_categoria

@router.delete("/{categoria_id}")
def delete_categoria_gasto_endpoint(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria = delete_categoria_gasto(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría de gasto not found")
    return {"message": "Categoría de gasto deleted"}
