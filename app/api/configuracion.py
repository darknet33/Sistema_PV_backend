from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.modulo import Modulo
from app.models.rol import Rol
from app.models.rol_modulo import RolModulo
from app.schemas.rol_modulo import RolModuloAssign, RolModuloResponse

router = APIRouter()

@router.get("/modulos", response_model=List[dict])
def get_all_modulos(db: Session = Depends(get_db)):
    modulos = db.query(Modulo).all()
    return [{"id": m.id, "nombre": m.nombre, "activo": m.activo} for m in modulos]

@router.get("/roles/{rol_id}/modulos", response_model=List[dict])
def get_modulos_by_rol(rol_id: int, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    modulos_asignados = db.query(RolModulo).filter(RolModulo.rol_id == rol_id).all()
    return [{"rol_id": rm.rol_id, "modulo_id": rm.modulo_id} for rm in modulos_asignados]

@router.put("/roles/{rol_id}/modulos", response_model=dict)
def asignar_modulos_a_rol(rol_id: int, payload: RolModuloAssign, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    db.query(RolModulo).filter(RolModulo.rol_id == rol_id).delete()
    db.flush()

    for modulo_id in payload.modulo_ids:
        modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
        if modulo:
            rol_modulo = RolModulo(rol_id=rol_id, modulo_id=modulo_id)
            db.add(rol_modulo)

    db.commit()
    return {"message": f"Módulos asignados al rol {rol.nombre}", "modulo_ids": payload.modulo_ids}

@router.post("/roles/{rol_id}/modulos/{modulo_id}", response_model=RolModuloResponse)
def agregar_modulo_a_rol(rol_id: int, modulo_id: int, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    existente = db.query(RolModulo).filter(
        RolModulo.rol_id == rol_id,
        RolModulo.modulo_id == modulo_id
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El módulo ya está asignado a este rol")

    rol_modulo = RolModulo(rol_id=rol_id, modulo_id=modulo_id)
    db.add(rol_modulo)
    db.commit()
    db.refresh(rol_modulo)
    return rol_modulo

@router.delete("/roles/{rol_id}/modulos/{modulo_id}", response_model=dict)
def quitar_modulo_de_rol(rol_id: int, modulo_id: int, db: Session = Depends(get_db)):
    rol_modulo = db.query(RolModulo).filter(
        RolModulo.rol_id == rol_id,
        RolModulo.modulo_id == modulo_id
    ).first()
    if not rol_modulo:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    db.delete(rol_modulo)
    db.commit()
    return {"message": "Módulo quitado del rol"}
