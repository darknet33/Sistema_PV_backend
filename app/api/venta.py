from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.schemas.venta import VentaCreate, VentaUpdate, VentaResponse
from app.crud.venta import get_ventas, get_venta, create_venta, update_venta, anular_venta, delete_venta
from app.ws import broadcast_multiple_sync
from datetime import datetime
from app.auth import get_current_user_full

router = APIRouter()

@router.get("/", response_model=List[VentaResponse])
def read_ventas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_ventas(db, skip, limit)

@router.get("/{venta_id}", response_model=VentaResponse)
def read_venta(venta_id: int, db: Session = Depends(get_db)):
    db_venta = get_venta(db, venta_id)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    return db_venta

@router.post("/", response_model=VentaResponse)
def create_venta_endpoint(venta: VentaCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user_full)):
    result = create_venta(db, venta, usuario_id=current_user.id)
    broadcast_multiple_sync(["ventas", "dashboard", "reportes"], {"type": "created", "room": "ventas"})
    return result

@router.put("/{venta_id}", response_model=VentaResponse)
def update_venta_endpoint(venta_id: int, venta: VentaUpdate, db: Session = Depends(get_db)):
    db_venta = update_venta(db, venta_id, venta)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    broadcast_multiple_sync(["ventas", "dashboard", "reportes"], {"type": "updated", "room": "ventas"})
    return db_venta

@router.put("/{venta_id}/anular", response_model=VentaResponse)
def anular_venta_endpoint(venta_id: int, db: Session = Depends(get_db)):
    db_venta = anular_venta(db, venta_id)
    if not db_venta:
        raise HTTPException(status_code=404, detail="Venta not found")
    broadcast_multiple_sync(["ventas", "dashboard", "reportes"], {"type": "updated", "room": "ventas"})
    return db_venta

@router.delete("/{venta_id}")
def delete_venta_endpoint(venta_id: int, db: Session = Depends(get_db)):
    result = delete_venta(db, venta_id)
    if not result:
        raise HTTPException(status_code=404, detail="Venta not found")
    broadcast_multiple_sync(["ventas", "dashboard", "reportes"], {"type": "deleted", "room": "ventas"})
    return result

@router.get("/{venta_id}/pdf")
def descargar_pdf_venta(venta_id: int, db: Session = Depends(get_db)):
    try:
        from app.reports.venta_single import generar_comprobante_venta
        buffer = generar_comprobante_venta(db, venta_id)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=venta_{venta_id}.pdf'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
