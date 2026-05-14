from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.proveedor import ProveedorCreate, ProveedorResponse
from app.crud.proveedor import get_proveedores, get_proveedor, create_proveedor, update_proveedor, delete_proveedor

router = APIRouter()

@router.get("/", response_model=List[ProveedorResponse])
def read_proveedores(skip: int = 0, limit: int = 100, solo_activos: bool = Query(False), db: Session = Depends(get_db)):
    return get_proveedores(db, skip, limit, solo_activos)

@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def read_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    db_proveedor = get_proveedor(db, proveedor_id)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return db_proveedor

@router.post("/", response_model=ProveedorResponse)
def create_proveedor_endpoint(proveedor: ProveedorCreate, db: Session = Depends(get_db)):
    return create_proveedor(db, proveedor)

@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def update_proveedor_endpoint(proveedor_id: int, proveedor: ProveedorCreate, db: Session = Depends(get_db)):
    db_proveedor = update_proveedor(db, proveedor_id, proveedor)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return db_proveedor

@router.delete("/{proveedor_id}")
def delete_proveedor_endpoint(proveedor_id: int, db: Session = Depends(get_db)):
    db_proveedor = delete_proveedor(db, proveedor_id)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    return {"message": "Proveedor deleted"}

@router.patch("/{proveedor_id}/toggle-activo", response_model=ProveedorResponse)
def toggle_proveedor_activo(proveedor_id: int, db: Session = Depends(get_db)):
    db_proveedor = get_proveedor(db, proveedor_id)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor not found")
    db_proveedor.activo = not db_proveedor.activo
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor
