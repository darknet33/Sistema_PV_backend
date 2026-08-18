from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.models.producto import Producto
from app.models.compra import Compra
from app.models.compra_detalle import CompraDetalle
from app.models.venta import Venta
from app.models.venta_detalle import VentaDetalle
from app.models.comprobante import Comprobante
from app.models.estado import Estado
def _sin_anuladas():
    return func.upper(Estado.nombre) != 'ANULADO'

def _query_entradas(db: Session, producto_id: int):
    return db.query(
        Compra.fecha,
        CompraDetalle.cantidad,
        CompraDetalle.costo,
        Comprobante.nombre.label('tipo_comprobante'),
        Compra.num_comprobante
    ).join(CompraDetalle, Compra.id == CompraDetalle.compra_id)\
     .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
     .join(Estado, Compra.estado_id == Estado.id)\
     .filter(CompraDetalle.producto_id == producto_id,
             _sin_anuladas())

def _query_salidas(db: Session, producto_id: int):
    return db.query(
        Venta.fecha,
        VentaDetalle.cantidad,
        VentaDetalle.precio,
        Comprobante.nombre.label('tipo_comprobante'),
        Venta.num_comprobante
    ).join(VentaDetalle, Venta.id == VentaDetalle.venta_id)\
     .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
     .join(Estado, Venta.estado_id == Estado.id)\
     .filter(VentaDetalle.producto_id == producto_id,
             _sin_anuladas())

def obtener_kardex(db: Session, producto_id: int, fecha_inicio: datetime = None, fecha_fin: datetime = None):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return None

    if not fecha_inicio:
        fecha_inicio = producto.fecha_registro or datetime(2000, 1, 1)
    if not fecha_fin:
        fecha_fin = datetime.now()

    entradas_previas = sum(
        e.cantidad for e in _query_entradas(db, producto_id)
        .filter(Compra.fecha < fecha_inicio).all()
    )
    salidas_previas = sum(
        s.cantidad for s in _query_salidas(db, producto_id)
        .filter(Venta.fecha < fecha_inicio).all()
    )
    saldo_inicial = producto.stock_inicial + entradas_previas - salidas_previas

    entradas = _query_entradas(db, producto_id)\
        .filter(Compra.fecha.between(fecha_inicio, fecha_fin)).all()

    salidas = _query_salidas(db, producto_id)\
        .filter(Venta.fecha.between(fecha_inicio, fecha_fin)).all()

    movimientos = [
        {
            'fecha': fecha_inicio,
            'tipo': 'SALDO INICIAL',
            'detalle': 'Stock inicial',
            'cantidad': 0,
            'precio': 0,
            'saldo': saldo_inicial,
        }
    ]
    saldo = saldo_inicial

    for e in entradas:
        saldo += e.cantidad
        movimientos.append({
            'fecha': e.fecha,
            'tipo': 'ENTRADA',
            'detalle': f"{e.tipo_comprobante} {e.num_comprobante}",
            'cantidad': e.cantidad,
            'precio': e.costo,
            'saldo': saldo
        })

    for s in salidas:
        saldo -= s.cantidad
        movimientos.append({
            'fecha': s.fecha,
            'tipo': 'SALIDA',
            'detalle': f"{s.tipo_comprobante} {s.num_comprobante}",
            'cantidad': s.cantidad,
            'precio': s.precio,
            'saldo': saldo
        })

    movimientos = sorted(movimientos, key=lambda x: x['fecha'])
    return {
        'producto': {
            'id': producto.id,
            'codigo': producto.codigo,
            'descripcion': producto.descripcion,
            'marca': producto.marca,
            'procedencia': producto.procedencia,
            'categoria': producto.categoria.nombre if producto.categoria else None,
            'precio': producto.precio,
            'utilidad': producto.utilidad,
            'stock_inicial': producto.stock_inicial,
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'stock_maximo': producto.stock_maximo,
            'imagen': producto.imagen,
            'activo': producto.activo,
        },
        'movimientos': movimientos,
    }
