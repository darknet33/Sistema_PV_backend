from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.gasto import Gasto
from app.models.categoria_gasto import CategoriaGasto
from app.models.estado import Estado
from app.models.usuario import Usuario
from app.schemas.gasto import GastoCreate, GastoUpdate

def _validate_foreign_keys(db: Session, categoria_gasto_id: int, estado_id: int):
    categoria = db.query(CategoriaGasto).filter(CategoriaGasto.id == categoria_gasto_id).first()
    if not categoria:
        raise HTTPException(status_code=400, detail=f"Categoría de gasto {categoria_gasto_id} no existe")

    estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if not estado:
        raise HTTPException(status_code=400, detail=f"Estado {estado_id} no existe")

def _build_response(db: Session, gasto: Gasto):
    categoria = db.query(CategoriaGasto).filter(CategoriaGasto.id == gasto.categoria_gasto_id).first()
    estado = db.query(Estado).filter(Estado.id == gasto.estado_id).first()
    usuario = db.query(Usuario).filter(Usuario.id == gasto.usuario_id).first()

    return {
        "id": gasto.id,
        "fecha": gasto.fecha,
        "categoria_gasto_id": gasto.categoria_gasto_id,
        "categoria_nombre": categoria.nombre if categoria else "",
        "descripcion": gasto.descripcion,
        "monto": gasto.monto or 0,
        "estado_id": gasto.estado_id,
        "estado_nombre": estado.nombre if estado else "",
        "activo": bool(gasto.activo),
        "usuario_id": gasto.usuario_id,
        "usuario_username": usuario.username if usuario else "",
        "fecha_registro": gasto.fecha_registro,
    }

def _get_estado_anulado(db: Session):
    estado = db.query(Estado).filter(Estado.nombre == "Anulado").first()
    if not estado:
        estado = Estado(nombre="Anulado")
        db.add(estado)
        db.flush()
    return estado

def get_gasto(db: Session, gasto_id: int):
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        return None
    return _build_response(db, gasto)

def get_gastos(db: Session, skip: int = 0, limit: int = 100):
    gastos = db.query(Gasto).order_by(Gasto.id.desc()).offset(skip).limit(limit).all()
    return [_build_response(db, g) for g in gastos]

def create_gasto(db: Session, gasto: GastoCreate, usuario_id: int):
    _validate_foreign_keys(db, gasto.categoria_gasto_id, gasto.estado_id)

    fecha = gasto.fecha if isinstance(gasto.fecha, datetime) else datetime.combine(gasto.fecha, datetime.min.time())
    fecha = datetime.combine(fecha.date(), datetime.now().time())

    db_gasto = Gasto(
        fecha=fecha,
        categoria_gasto_id=gasto.categoria_gasto_id,
        descripcion=gasto.descripcion,
        monto=gasto.monto,
        estado_id=gasto.estado_id,
        usuario_id=usuario_id,
        activo=1,
    )
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return _build_response(db, db_gasto)

def update_gasto(db: Session, gasto_id: int, gasto: GastoUpdate):
    db_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not db_gasto:
        return None

    categoria_gasto_id = gasto.categoria_gasto_id if gasto.categoria_gasto_id is not None else db_gasto.categoria_gasto_id
    estado_id = gasto.estado_id if gasto.estado_id is not None else db_gasto.estado_id
    _validate_foreign_keys(db, categoria_gasto_id, estado_id)

    if gasto.fecha is not None:
        fecha = gasto.fecha if isinstance(gasto.fecha, datetime) else datetime.combine(gasto.fecha, datetime.min.time())
        db_gasto.fecha = datetime.combine(fecha.date(), datetime.now().time())
    if gasto.categoria_gasto_id is not None:
        db_gasto.categoria_gasto_id = gasto.categoria_gasto_id
    if gasto.descripcion is not None:
        db_gasto.descripcion = gasto.descripcion
    if gasto.monto is not None:
        db_gasto.monto = gasto.monto
    if gasto.estado_id is not None:
        db_gasto.estado_id = gasto.estado_id
        db_gasto.activo = 0 if gasto.estado_id == _get_estado_anulado(db).id else 1

    db.commit()
    db.refresh(db_gasto)
    return _build_response(db, db_gasto)

def anular_gasto(db: Session, gasto_id: int):
    db_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not db_gasto:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_gasto.estado_id == estado_anulado.id:
        raise HTTPException(status_code=400, detail="El gasto ya está anulado")

    db_gasto.estado_id = estado_anulado.id
    db_gasto.activo = 0
    db.commit()
    db.refresh(db_gasto)
    return _build_response(db, db_gasto)

def delete_gasto(db: Session, gasto_id: int):
    db_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not db_gasto:
        return None

    estado_anulado = _get_estado_anulado(db)
    if db_gasto.estado_id != estado_anulado.id:
        raise HTTPException(status_code=400, detail="Solo se puede eliminar gastos anulados")

    db.delete(db_gasto)
    db.commit()
    return {"message": "Gasto deleted"}
