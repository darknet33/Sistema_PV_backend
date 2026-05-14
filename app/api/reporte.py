from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from app.database import get_db
from datetime import datetime
from typing import Optional
import io

router = APIRouter()

@router.get("/kardex/{producto_id}")
def get_kardex(producto_id: int, fecha_inicio: datetime, fecha_fin: datetime, db: Session = Depends(get_db)):
    try:
        from app.reports.kardex import generar_kardex
        buffer = generar_kardex(db, producto_id, fecha_inicio, fecha_fin)
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=kardex_{producto_id}.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
