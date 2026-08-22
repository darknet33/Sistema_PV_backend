from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.categoria_gasto import CategoriaGasto
from app.models.gasto import Gasto
from app.schemas.categoria_gasto import CategoriaGastoCreate
from app.utils import capitalizar

def get_categoria_gasto(db: Session, categoria_id: int):
    return db.query(CategoriaGasto).filter(CategoriaGasto.id == categoria_id).first()

def get_categorias_gastos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(CategoriaGasto).offset(skip).limit(limit).all()

def create_categoria_gasto(db: Session, categoria: CategoriaGastoCreate):
    existe = db.query(CategoriaGasto).filter(CategoriaGasto.nombre == capitalizar(categoria.nombre)).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe una categoría de gasto con ese nombre")
    db_categoria = CategoriaGasto(nombre=capitalizar(categoria.nombre))
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def update_categoria_gasto(db: Session, categoria_id: int, categoria: CategoriaGastoCreate):
    db_categoria = get_categoria_gasto(db, categoria_id)
    if db_categoria:
        db_categoria.nombre = capitalizar(categoria.nombre)
        db.commit()
        db.refresh(db_categoria)
    return db_categoria

def delete_categoria_gasto(db: Session, categoria_id: int):
    db_categoria = get_categoria_gasto(db, categoria_id)
    if db_categoria:
        en_gastos = db.query(Gasto).filter(Gasto.categoria_gasto_id == categoria_id).first()
        if en_gastos:
            raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene gastos asociados")
        db.delete(db_categoria)
        db.commit()
    return db_categoria
