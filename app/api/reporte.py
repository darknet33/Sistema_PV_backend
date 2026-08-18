from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from app.database import get_db
from datetime import datetime, date, timedelta
from typing import Optional
import io

router = APIRouter()

@router.get("/kardex/{producto_id}")
def get_kardex(producto_id: int, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None, db: Session = Depends(get_db)):
    from app.models.producto import Producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    fi = fecha_inicio or (producto.fecha_registro or datetime(2000, 1, 1))
    ff = fecha_fin or datetime.now()
    try:
        from app.reports.kardex import generar_kardex
        buffer = generar_kardex(db, producto_id, fi, ff)
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=kardex_{producto_id}.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kardex/{producto_id}/movimientos")
def get_kardex_movimientos(producto_id: int, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None, db: Session = Depends(get_db)):
    from app.services.kardex import obtener_kardex
    resultado = obtener_kardex(db, producto_id, fecha_inicio, fecha_fin)
    if not resultado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return resultado

@router.get("/ventas/pdf")
def reporte_ventas_pdf(fecha_inicio: datetime, fecha_fin: datetime, cliente_text: Optional[str] = Query(None), estado_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        from app.reports.ventas import generar_reporte_ventas
        buffer = generar_reporte_ventas(db, fecha_inicio, fecha_fin, cliente_text, estado_id)
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename=reporte_ventas.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compras/pdf")
def reporte_compras_pdf(fecha_inicio: datetime, fecha_fin: datetime, proveedor_text: Optional[str] = Query(None), estado_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        from app.reports.compras import generar_reporte_compras
        buffer = generar_reporte_compras(db, fecha_inicio, fecha_fin, proveedor_text, estado_id)
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': 'attachment; filename=reporte_compras.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumen/ventas")
def resumen_ventas_json(fecha_inicio: datetime, fecha_fin: datetime, cliente_text: Optional[str] = Query(None), estado_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    from app.services.reportes import resumen_ventas
    return resumen_ventas(db, fecha_inicio, fecha_fin)

@router.get("/resumen/compras")
def resumen_compras_json(fecha_inicio: datetime, fecha_fin: datetime, proveedor_text: Optional[str] = Query(None), estado_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    from app.services.reportes import resumen_compras
    return resumen_compras(db, fecha_inicio, fecha_fin)

@router.get("/resumen/top-productos")
def top_productos_json(fecha_inicio: datetime, fecha_fin: datetime, limite: int = Query(10), db: Session = Depends(get_db)):
    from app.services.reportes import productos_mas_vendidos
    return productos_mas_vendidos(db, fecha_inicio, fecha_fin, limite)

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    from app.models.venta import Venta
    from app.models.venta_detalle import VentaDetalle
    from app.models.compra import Compra
    from app.models.producto import Producto
    from app.models.usuario import Usuario
    from sqlalchemy import func

    hoy = date.today()
    inicio_hoy = datetime(hoy.year, hoy.month, hoy.day, 0, 0, 0)
    fin_hoy = datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59)

    inicio_30d = inicio_hoy - timedelta(days=29)

    # Resumen hoy
    ventas_hoy = db.query(func.count(Venta.id), func.coalesce(func.sum(Venta.total), 0)).filter(Venta.fecha.between(inicio_hoy, fin_hoy)).first()
    compras_hoy = db.query(func.count(Compra.id), func.coalesce(func.sum(Compra.total), 0)).filter(Compra.fecha.between(inicio_hoy, fin_hoy)).first()

    # Ventas por dia (últimos 30 días)
    ventas_por_dia = db.query(
        func.date(Venta.fecha).label('fecha'),
        func.count(Venta.id).label('cantidad'),
        func.coalesce(func.sum(Venta.total), 0).label('total'),
    ).filter(Venta.fecha.between(inicio_30d, fin_hoy)).group_by(func.date(Venta.fecha)).order_by(func.date(Venta.fecha)).all()

    # Compras por dia (últimos 30 días)
    compras_por_dia = db.query(
        func.date(Compra.fecha).label('fecha'),
        func.count(Compra.id).label('cantidad'),
        func.coalesce(func.sum(Compra.total), 0).label('total'),
    ).filter(Compra.fecha.between(inicio_30d, fin_hoy)).group_by(func.date(Compra.fecha)).order_by(func.date(Compra.fecha)).all()

    # Top vendedores
    top_vendedores = db.query(
        Usuario.username,
        func.count(Venta.id).label('cantidad'),
        func.coalesce(func.sum(Venta.total), 0).label('total'),
    ).join(Venta, Usuario.id == Venta.usuario_id).filter(Venta.fecha.between(inicio_30d, fin_hoy)).group_by(Usuario.id).order_by(func.sum(Venta.total).desc()).limit(10).all()

    # Stock bajo
    stock_bajo = db.query(Producto).filter(Producto.stock_actual < Producto.stock_minimo).order_by(Producto.stock_actual.asc()).all()

    return {
        'resumen_hoy': {
            'ventas_cantidad': ventas_hoy[0],
            'ventas_total': float(ventas_hoy[1]),
            'compras_cantidad': compras_hoy[0],
            'compras_total': float(compras_hoy[1]),
        },
        'ventas_por_dia': [{'fecha': str(r.fecha), 'cantidad': r.cantidad, 'total': float(r.total)} for r in ventas_por_dia],
        'compras_por_dia': [{'fecha': str(r.fecha), 'cantidad': r.cantidad, 'total': float(r.total)} for r in compras_por_dia],
        'top_vendedores': [{'username': r.username, 'cantidad': r.cantidad, 'total': float(r.total)} for r in top_vendedores],
        'stock_bajo': [{
            'id': p.id,
            'codigo': p.codigo,
            'descripcion': p.descripcion,
            'marca': p.marca,
            'stock_actual': p.stock_actual,
            'stock_minimo': p.stock_minimo,
        } for p in stock_bajo],
    }
