from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from app.crud.producto import get_productos, get_producto, get_producto_by_codigo, create_producto, update_producto, delete_producto

router = APIRouter()

@router.get("/", response_model=List[ProductoResponse])
def read_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_productos(db, skip, limit)

@router.get("/{producto_id}", response_model=ProductoResponse)
def read_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.get("/codigo/{codigo}", response_model=ProductoResponse)
def read_producto_by_codigo(codigo: str, db: Session = Depends(get_db)):
    db_producto = get_producto_by_codigo(db, codigo)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.post("/", response_model=ProductoResponse)
def create_producto_endpoint(producto: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = get_producto_by_codigo(db, producto.codigo)
    if db_producto:
        raise HTTPException(status_code=400, detail="Codigo already registered")
    return create_producto(db, producto)

@router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto_endpoint(producto_id: int, producto: ProductoUpdate, db: Session = Depends(get_db)):
    db_producto = update_producto(db, producto_id, producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.delete("/{producto_id}")
def delete_producto_endpoint(producto_id: int, db: Session = Depends(get_db)):
    db_producto = delete_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return {"message": "Producto deleted"}
