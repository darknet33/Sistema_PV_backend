from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.schemas.categoria import CategoriaCreate
from app.utils import capitalizar

def get_categoria(db: Session, categoria_id: int):
    return db.query(Categoria).filter(Categoria.id == categoria_id).first()

def get_categorias(db: Session, skip: int = 0, limit: int = 10000):
    return db.query(Categoria).offset(skip).limit(limit).all()

def create_categoria(db: Session, categoria: CategoriaCreate):
    db_categoria = Categoria(nombre=capitalizar(categoria.nombre))
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def update_categoria(db: Session, categoria_id: int, categoria: CategoriaCreate):
    db_categoria = get_categoria(db, categoria_id)
    if db_categoria:
        db_categoria.nombre = capitalizar(categoria.nombre)
        db.commit()
        db.refresh(db_categoria)
    return db_categoria

def delete_categoria(db: Session, categoria_id: int):
    db_categoria = get_categoria(db, categoria_id)
    if not db_categoria:
        return None
    tiene_productos = db.query(Producto).filter(Producto.categoria_id == categoria_id).first()
    if tiene_productos:
        raise HTTPException(status_code=400, detail="No se puede eliminar porque tiene productos asociados")
    db.delete(db_categoria)
    db.commit()
    return db_categoria

def delete_all_categorias(db: Session):
    categorias = db.query(Categoria).all()
    eliminadas = 0
    omitidas = []
    for cat in categorias:
        tiene_productos = db.query(Producto).filter(Producto.categoria_id == cat.id).first()
        if tiene_productos:
            omitidas.append(cat.nombre)
        else:
            db.delete(cat)
            eliminadas += 1
    db.commit()
    return {"eliminadas": eliminadas, "omitidas": omitidas}
