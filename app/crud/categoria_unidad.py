from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.categoria_unidad import CategoriaUnidad
from app.models.unidad_medida import UnidadMedida
from app.schemas.categoria_unidad import CategoriaUnidadCreate
from app.utils import capitalizar


def get_categoria_unidad(db: Session, cat_id: int):
    return db.query(CategoriaUnidad).filter(CategoriaUnidad.id == cat_id).first()


def get_categorias_unidad(db: Session, skip: int = 0, limit: int = 10000):
    return db.query(CategoriaUnidad).offset(skip).limit(limit).all()


def create_categoria_unidad(db: Session, data: CategoriaUnidadCreate):
    db_obj = CategoriaUnidad(nombre=capitalizar(data.nombre), descripcion=capitalizar(data.descripcion))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_categoria_unidad(db: Session, cat_id: int, data: CategoriaUnidadCreate):
    db_obj = get_categoria_unidad(db, cat_id)
    if not db_obj:
        return None
    db_obj.nombre = capitalizar(data.nombre)
    db_obj.descripcion = capitalizar(data.descripcion)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_categoria_unidad(db: Session, cat_id: int):
    db_obj = get_categoria_unidad(db, cat_id)
    if not db_obj:
        return None
    tiene = db.query(UnidadMedida).filter(UnidadMedida.categoria_unidad_id == cat_id).first()
    if tiene:
        raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene unidades asociadas")
    db.delete(db_obj)
    db.commit()
    return db_obj


def delete_all_categorias_unidad(db: Session):
    cats = db.query(CategoriaUnidad).all()
    eliminadas = 0
    omitidas = []
    for cat in cats:
        tiene = db.query(UnidadMedida).filter(UnidadMedida.categoria_unidad_id == cat.id).first()
        if tiene:
            omitidas.append(cat.nombre)
        else:
            db.delete(cat)
            eliminadas += 1
    db.commit()
    return {"eliminadas": eliminadas, "omitidas": omitidas}
