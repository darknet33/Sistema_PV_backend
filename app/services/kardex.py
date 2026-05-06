from sqlalchemy.orm import Session
from datetime import datetime
from app.models.producto import Producto
from app.models.compra import Compra
from app.models.compra_detalle import CompraDetalle
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.models.comprobante import Comprobante

def obtener_kardex(db: Session, producto_id: int, fecha_inicio: datetime, fecha_fin: datetime):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return None
    
    entradas = db.query(
        Compra.fecha,
        CompraDetalle.cantidad,
        CompraDetalle.costo,
        Comprobante.nombre.label('tipo_comprobante'),
        Compra.num_comprobante
    ).join(CompraDetalle, Compra.id == CompraDetalle.compra_id)\
     .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
     .filter(CompraDetalle.producto_id == producto_id,
             Compra.fecha.between(fecha_inicio, fecha_fin)).all()
    
    salidas = db.query(
        Venta.fecha,
        VentaDetalle.cantidad,
        VentaDetalle.precio,
        Comprobante.nombre.label('tipo_comprobante'),
        Venta.num_comprobante
    ).join(VentaDetalle, Venta.id == VentaDetalle.venta_id)\
     .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
     .filter(VentaDetalle.producto_id == producto_id,
             Venta.fecha.between(fecha_inicio, fecha_fin)).all()
    
    kardex = []
    saldo = producto.stock_inicial
    
    for e in entradas:
        saldo += e.cantidad
        kardex.append({
            'fecha': e.fecha,
            'tipo': 'ENTRADA',
            'detalle': f"{e.tipo_comprobante} {e.num_comprobante}",
            'cantidad': e.cantidad,
            'precio': e.costo,
            'saldo': saldo
        })
    
    for s in salidas:
        saldo -= s.cantidad
        kardex.append({
            'fecha': s.fecha,
            'tipo': 'SALIDA',
            'detalle': f"{s.tipo_comprobante} {s.num_comprobante}",
            'cantidad': s.cantidad,
            'precio': s.precio,
            'saldo': saldo
        })
    
    return sorted(kardex, key=lambda x: x['fecha'])
