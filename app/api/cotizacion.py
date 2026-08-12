from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.schemas.cotizacion import CotizacionCreate, CotizacionUpdate, CotizacionResponse, ConvertirVentaRequest
from app.crud.cotizacion import get_cotizaciones, get_cotizacion, create_cotizacion, update_cotizacion, confirmar_cotizacion, delete_cotizacion, convertir_en_venta
from app.ws import broadcast_multiple_sync

router = APIRouter()


@router.get("/", response_model=List[CotizacionResponse])
def read_cotizaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_cotizaciones(db, skip, limit)


@router.get("/{cotizacion_id}", response_model=CotizacionResponse)
def read_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    db_cotizacion = get_cotizacion(db, cotizacion_id)
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotización not found")
    return db_cotizacion


@router.post("/", response_model=CotizacionResponse)
def create_cotizacion_endpoint(cotizacion: CotizacionCreate, db: Session = Depends(get_db)):
    result = create_cotizacion(db, cotizacion, usuario_id=1)
    broadcast_multiple_sync(["cotizaciones"], {"type": "created", "room": "cotizaciones"})
    return result


@router.put("/{cotizacion_id}", response_model=CotizacionResponse)
def update_cotizacion_endpoint(cotizacion_id: int, cotizacion: CotizacionUpdate, db: Session = Depends(get_db)):
    db_cotizacion = update_cotizacion(db, cotizacion_id, cotizacion)
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotización not found")
    broadcast_multiple_sync(["cotizaciones"], {"type": "updated", "room": "cotizaciones"})
    return db_cotizacion


@router.put("/{cotizacion_id}/confirmar", response_model=CotizacionResponse)
def confirmar_cotizacion_endpoint(cotizacion_id: int, db: Session = Depends(get_db)):
    db_cotizacion = confirmar_cotizacion(db, cotizacion_id)
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotización not found")
    broadcast_multiple_sync(["cotizaciones"], {"type": "updated", "room": "cotizaciones"})
    return db_cotizacion


@router.delete("/{cotizacion_id}", response_model=CotizacionResponse)
def delete_cotizacion_endpoint(cotizacion_id: int, db: Session = Depends(get_db)):
    db_cotizacion = delete_cotizacion(db, cotizacion_id)
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotización not found")
    broadcast_multiple_sync(["cotizaciones"], {"type": "deleted", "room": "cotizaciones"})
    return db_cotizacion


@router.post("/{cotizacion_id}/convertir-venta")
def convertir_venta_endpoint(cotizacion_id: int, payload: ConvertirVentaRequest, db: Session = Depends(get_db)):
    from app.schemas.venta import VentaResponse
    result = convertir_en_venta(db, cotizacion_id, payload, usuario_id=1)
    if not result:
        raise HTTPException(status_code=404, detail="Cotización not found")
    broadcast_multiple_sync(["cotizaciones", "ventas", "dashboard", "reportes"], {"type": "created", "room": "ventas"})
    return VentaResponse.model_validate(result)


@router.get("/{cotizacion_id}/pdf")
def descargar_pdf_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    try:
        from app.reports.cotizacion_single import generar_pdf_cotizacion
        buffer = generar_pdf_cotizacion(db, cotizacion_id)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=cotizacion_{cotizacion_id}.pdf'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cotizacion_id}/pdf/preview")
def vista_previa_pdf_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    try:
        from app.reports.cotizacion_single import generar_pdf_cotizacion
        buffer = generar_pdf_cotizacion(db, cotizacion_id)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'inline; filename=cotizacion_{cotizacion_id}.pdf'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
