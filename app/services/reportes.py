from sqlalchemy.orm import Session
from datetime import datetime
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.models.cliente import Cliente
from app.models.comprobante import Comprobante
from app.models.estado import Estado
from app.models.compra import Compra
from app.models.compra_detalle import CompraDetalle
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.categoria import Categoria

def resumen_ventas(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    ventas = db.query(Venta, Cliente, Comprobante, Estado)\
        .join(Cliente, Venta.cliente_id == Cliente.id)\
        .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
        .join(Estado, Venta.estado_id == Estado.id)\
        .filter(Venta.fecha.between(fecha_inicio, fecha_fin))\
        .order_by(Venta.fecha.desc()).all()
    
    resultados = []
    for v, c, comp, e in ventas:
        detalles = db.query(VentaDetalle).filter(VentaDetalle.venta_id == v.id).all()
        subtotal = sum(d.cantidad * d.precio for d in detalles)
        resultados.append({
            'venta_id': v.id,
            'fecha': v.fecha,
            'num_comprobante': v.num_comprobante,
            'cliente': c.nombre,
            'tipo_comprobante': comp.nombre,
            'estado': e.nombre,
            'subtotal': subtotal,
            'impuesto': v.impuesto,
            'descuento': v.descuento,
            'total': v.total,
            'utilidad': sum(d.utilidad * d.cantidad for d in detalles)
        })
    return resultados

def resumen_compras(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    compras = db.query(Compra, Proveedor, Comprobante, Estado)\
        .join(Proveedor, Compra.proveedor_id == Proveedor.id)\
        .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
        .join(Estado, Compra.estado_id == Estado.id)\
        .filter(Compra.fecha.between(fecha_inicio, fecha_fin))\
        .order_by(Compra.fecha.desc()).all()
    
    resultados = []
    for c, p, comp, e in compras:
        resultados.append({
            'compra_id': c.id,
            'fecha': c.fecha,
            'num_comprobante': c.num_comprobante,
            'proveedor': p.nombre,
            'tipo_comprobante': comp.nombre,
            'estado': e.nombre,
            'total': c.total
        })
    return resultados

def productos_mas_vendidos(db: Session, fecha_inicio: datetime, fecha_fin: datetime, limite: int = 10):
    from sqlalchemy import func
    
    resultados = db.query(
        Producto.id,
        Producto.codigo,
        Producto.descripcion,
        Producto.marca,
        Categoria.nombre.label('categoria'),
        func.sum(VentaDetalle.cantidad).label('total_vendido')
    ).join(VentaDetalle, Producto.id == VentaDetalle.producto_id)\
     .join(Venta, VentaDetalle.venta_id == Venta.id)\
     .outerjoin(Categoria, Producto.categoria_id == Categoria.id)\
     .filter(Venta.fecha.between(fecha_inicio, fecha_fin))\
     .group_by(Producto.id)\
     .order_by(func.sum(VentaDetalle.cantidad).desc())\
     .limit(limite).all()
    
    return [
        {
            'id': r.id,
            'codigo': r.codigo,
            'descripcion': f"{r.codigo} {r.categoria if r.categoria else 'SinCategoria'} {r.descripcion} {r.marca}",
            'total_vendido': r.total_vendido
        } for r in resultados
    ]
