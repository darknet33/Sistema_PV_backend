from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.rol import RolCreate, RolResponse
from app.crud.rol import get_roles, get_rol, create_rol, update_rol, delete_rol

router = APIRouter()

@router.get("/", response_model=List[RolResponse])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_roles(db, skip, limit)

@router.get("/{rol_id}", response_model=RolResponse)
def read_rol(rol_id: int, db: Session = Depends(get_db)):
    db_rol = get_rol(db, rol_id)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol not found")
    return db_rol

@router.post("/", response_model=RolResponse)
def create_rol_endpoint(rol: RolCreate, db: Session = Depends(get_db)):
    return create_rol(db, rol)

@router.put("/{rol_id}", response_model=RolResponse)
def update_rol_endpoint(rol_id: int, rol: RolCreate, db: Session = Depends(get_db)):
    db_rol = update_rol(db, rol_id, rol)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol not found")
    return db_rol

@router.delete("/{rol_id}")
def delete_rol_endpoint(rol_id: int, db: Session = Depends(get_db)):
    db_rol = delete_rol(db, rol_id)
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol not found")
    return {"message": "Rol deleted"}
