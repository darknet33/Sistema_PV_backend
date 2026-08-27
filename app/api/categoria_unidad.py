from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.categoria_unidad import CategoriaUnidadCreate, CategoriaUnidadResponse
from app.crud.categoria_unidad import (
    get_categorias_unidad, get_categoria_unidad, create_categoria_unidad,
    update_categoria_unidad, delete_categoria_unidad, delete_all_categorias_unidad
)

router = APIRouter()


@router.get("/", response_model=List[CategoriaUnidadResponse])
def read_categorias(skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)):
    return get_categorias_unidad(db, skip, limit)


@router.get("/{cat_id}", response_model=CategoriaUnidadResponse)
def read_categoria(cat_id: int, db: Session = Depends(get_db)):
    db_obj = get_categoria_unidad(db, cat_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Categoría de unidad no encontrada")
    return db_obj


@router.post("/", response_model=CategoriaUnidadResponse)
def create_categoria_endpoint(data: CategoriaUnidadCreate, db: Session = Depends(get_db)):
    return create_categoria_unidad(db, data)


@router.put("/{cat_id}", response_model=CategoriaUnidadResponse)
def update_categoria_endpoint(cat_id: int, data: CategoriaUnidadCreate, db: Session = Depends(get_db)):
    db_obj = update_categoria_unidad(db, cat_id, data)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Categoría de unidad no encontrada")
    return db_obj


@router.delete("/all")
def delete_all_endpoint(db: Session = Depends(get_db)):
    resultado = delete_all_categorias_unidad(db)
    msg = f"{resultado['eliminadas']} categorías de unidad eliminadas"
    if resultado['omitidas']:
        msg += f", {len(resultado['omitidas'])} omitidas (tienen unidades): {', '.join(resultado['omitidas'])}"
    return {"message": msg, **resultado}


@router.delete("/{cat_id}")
def delete_categoria_endpoint(cat_id: int, db: Session = Depends(get_db)):
    db_obj = delete_categoria_unidad(db, cat_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Categoría de unidad no encontrada")
    return {"message": "Categoría de unidad eliminada"}
