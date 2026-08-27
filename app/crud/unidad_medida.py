from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.unidad_medida import UnidadMedida
from app.schemas.unidad_medida import UnidadMedidaCreate


def get_unidad_medida(db: Session, uid: int):
    return db.query(UnidadMedida).filter(UnidadMedida.id == uid).first()


def get_unidades_medida(db: Session, categoria_id: int = None, skip: int = 0, limit: int = 10000):
    q = db.query(UnidadMedida)
    if categoria_id is not None:
        q = q.filter(UnidadMedida.categoria_unidad_id == categoria_id)
    return q.offset(skip).limit(limit).all()


def create_unidad_medida(db: Session, data: UnidadMedidaCreate):
    db_obj = UnidadMedida(
        nombre=data.nombre,
        abreviatura=data.abreviatura,
        categoria_unidad_id=data.categoria_unidad_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_unidad_medida(db: Session, uid: int, data: UnidadMedidaCreate):
    db_obj = get_unidad_medida(db, uid)
    if not db_obj:
        return None
    db_obj.nombre = data.nombre
    db_obj.abreviatura = data.abreviatura
    db_obj.categoria_unidad_id = data.categoria_unidad_id
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_unidad_medida(db: Session, uid: int):
    db_obj = get_unidad_medida(db, uid)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


def delete_all_unidades_medida(db: Session):
    count = db.query(UnidadMedida).delete()
    db.commit()
    return {"eliminadas": count}
