from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaResponse
from app.crud.categoria import get_categorias, get_categoria, create_categoria, update_categoria, delete_categoria, delete_all_categorias

router = APIRouter()

@router.get("/", response_model=List[CategoriaResponse])
def read_categorias(skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)):
    return get_categorias(db, skip, limit)

@router.get("/{categoria_id}", response_model=CategoriaResponse)
def read_categoria(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria = get_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return db_categoria

@router.post("/", response_model=CategoriaResponse)
def create_categoria_endpoint(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    return create_categoria(db, categoria)

@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria_endpoint(categoria_id: int, categoria: CategoriaCreate, db: Session = Depends(get_db)):
    db_categoria = update_categoria(db, categoria_id, categoria)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return db_categoria

@router.delete("/all")
def delete_all_categorias_endpoint(db: Session = Depends(get_db)):
    resultado = delete_all_categorias(db)
    msg = f"{resultado['eliminadas']} categorías eliminadas"
    if resultado['omitidas']:
        msg += f", {len(resultado['omitidas'])} omitidas (tienen productos): {', '.join(resultado['omitidas'])}"
    return {"message": msg, **resultado}

@router.delete("/{categoria_id}")
def delete_categoria_endpoint(categoria_id: int, db: Session = Depends(get_db)):
    db_categoria = delete_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoria not found")
    return {"message": "Categoria deleted"}
