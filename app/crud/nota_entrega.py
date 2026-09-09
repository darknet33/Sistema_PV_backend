from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.nota_entrega import NotaEntrega, NotaEntregaDetalle
from app.models.venta import Venta
from app.models.producto import Producto
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.schemas.nota_entrega import NotaEntregaCreate
from app.utils import capitalizar


def _validate_foreign_keys(db: Session, venta_id: int, detalles: list):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=400, detail=f"Venta {venta_id} no existe")

    for detalle in detalles:
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if not producto:
            raise HTTPException(status_code=400, detail=f"Producto {detalle.producto_id} no existe")
        if not detalle.cantidad or int(detalle.cantidad) < 1:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {detalle.producto_id}")


def _build_response(db: Session, nota: NotaEntrega):
    detalles = db.query(NotaEntregaDetalle).filter(NotaEntregaDetalle.nota_entrega_id == nota.id).all()

    detalles_response = []
    total_cantidad = 0
    for d in detalles:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ""
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ""
        detalles_response.append({
            "id": d.id,
            "producto_id": d.producto_id,
            "producto_nombre": prod.descripcion if prod else "",
            "producto_codigo": prod.codigo if prod else "",
            "producto_categoria": cat_nombre,
            "cantidad": d.cantidad,
        })
        total_cantidad += d.cantidad

    usuario = db.query(Usuario).filter(Usuario.id == nota.usuario_id).first()

    return {
        "id": nota.id,
        "numero": nota.numero,
        "venta_id": nota.venta_id,
        "fecha": nota.fecha,
        "entregue_nombre": nota.entregue_nombre,
        "entregue_carnet": nota.entregue_carnet,
        "recibi_nombre": nota.recibi_nombre,
        "recibi_carnet": nota.recibi_carnet,
        "usuario_id": nota.usuario_id,
        "usuario_username": usuario.username if usuario else "",
        "activo": bool(nota.activo),
        "total_cantidad": total_cantidad,
        "fecha_registro": nota.fecha_registro,
        "detalles": detalles_response,
    }


def get_nota_entrega(db: Session, nota_id: int):
    nota = db.query(NotaEntrega).filter(NotaEntrega.id == nota_id).first()
    if not nota:
        return None
    return _build_response(db, nota)


def get_notas_entrega(db: Session, venta_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(NotaEntrega).order_by(NotaEntrega.id.desc())
    if venta_id is not None:
        query = query.filter(NotaEntrega.venta_id == venta_id)
    notas = query.offset(skip).limit(limit).all()
    return [_build_response(db, n) for n in notas]


def create_nota_entrega(db: Session, nota: NotaEntregaCreate, usuario_id: int):
    if not nota.detalles:
        raise HTTPException(status_code=400, detail="Debe agregar al menos un producto")
    _validate_foreign_keys(db, nota.venta_id, nota.detalles)

    venta = db.query(Venta).filter(Venta.id == nota.venta_id).first()

    fecha = nota.fecha or datetime.now()
    if not isinstance(fecha, datetime):
        fecha = datetime.combine(fecha, datetime.min.time())
    fecha = datetime.combine(fecha.date(), datetime.now().time())

    db_nota = NotaEntrega(
        numero="NE-000000",
        venta_id=nota.venta_id,
        fecha=fecha,
        entregue_nombre=capitalizar(nota.entregue_nombre.strip()),
        entregue_carnet=nota.entregue_carnet.strip(),
        recibi_nombre=capitalizar(nota.recibi_nombre.strip()),
        recibi_carnet=nota.recibi_carnet.strip(),
        usuario_id=usuario_id,
        activo=True,
    )
    db.add(db_nota)
    db.flush()

    db_nota.numero = f"NE-{db_nota.id:06d}"

    for detalle in nota.detalles:
        db_detalle = NotaEntregaDetalle(
            nota_entrega_id=db_nota.id,
            producto_id=detalle.producto_id,
            cantidad=int(detalle.cantidad),
        )
        db.add(db_detalle)

    db.commit()
    db.refresh(db_nota)
    return _build_response(db, db_nota)


def delete_nota_entrega(db: Session, nota_id: int):
    db_nota = db.query(NotaEntrega).filter(NotaEntrega.id == nota_id).first()
    if not db_nota:
        return None
    db.query(NotaEntregaDetalle).filter(NotaEntregaDetalle.nota_entrega_id == nota_id).delete()
    db.delete(db_nota)
    db.commit()
    return {"message": "Nota de entrega deleted"}
