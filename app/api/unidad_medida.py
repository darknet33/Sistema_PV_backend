from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.schemas.unidad_medida import UnidadMedidaCreate, UnidadMedidaResponse
from app.models.unidad_medida import UnidadMedida
from app.crud.unidad_medida import (
    get_unidades_medida, get_unidad_medida, create_unidad_medida,
    update_unidad_medida, delete_unidad_medida, delete_all_unidades_medida
)

router = APIRouter()


def _build_response(unidad: UnidadMedida) -> dict:
    return {
        "id": unidad.id,
        "nombre": unidad.nombre,
        "abreviatura": unidad.abreviatura or "",
        "categoria_unidad_id": unidad.categoria_unidad_id,
        "activo": bool(unidad.activo),
        "categoria_nombre": unidad.categoria.nombre if unidad.categoria else "",
    }


@router.get("/", response_model=List[UnidadMedidaResponse])
def read_unidades(categoria_id: int = None, skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)):
    objs = db.query(UnidadMedida).options(joinedload(UnidadMedida.categoria))
    if categoria_id is not None:
        objs = objs.filter(UnidadMedida.categoria_unidad_id == categoria_id)
    objs = objs.offset(skip).limit(limit).all()
    return [_build_response(u) for u in objs]


@router.get("/{uid}", response_model=UnidadMedidaResponse)
def read_unidad(uid: int, db: Session = Depends(get_db)):
    db_obj = get_unidad_medida(db, uid)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    db_obj_carga = db.query(UnidadMedida).options(joinedload(UnidadMedida.categoria)).filter(UnidadMedida.id == uid).first()
    return _build_response(db_obj_carga)


@router.post("/", response_model=UnidadMedidaResponse)
def create_unidad_endpoint(data: UnidadMedidaCreate, db: Session = Depends(get_db)):
    db_obj = create_unidad_medida(db, data)
    db_obj_carga = db.query(UnidadMedida).options(joinedload(UnidadMedida.categoria)).filter(UnidadMedida.id == db_obj.id).first()
    return _build_response(db_obj_carga)


@router.put("/{uid}", response_model=UnidadMedidaResponse)
def update_unidad_endpoint(uid: int, data: UnidadMedidaCreate, db: Session = Depends(get_db)):
    db_obj = update_unidad_medida(db, uid, data)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    db_obj_carga = db.query(UnidadMedida).options(joinedload(UnidadMedida.categoria)).filter(UnidadMedida.id == uid).first()
    return _build_response(db_obj_carga)


@router.delete("/all")
def delete_all_endpoint(db: Session = Depends(get_db)):
    resultado = delete_all_unidades_medida(db)
    return {"message": f"{resultado['eliminadas']} unidades eliminadas", **resultado}


@router.delete("/{uid}")
def delete_unidad_endpoint(uid: int, db: Session = Depends(get_db)):
    db_obj = delete_unidad_medida(db, uid)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    return {"message": "Unidad de medida eliminada"}
