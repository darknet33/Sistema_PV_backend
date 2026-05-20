from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.schemas.compra import CompraCreate, CompraUpdate, CompraResponse
from app.crud.compra import get_compras, get_compra, create_compra, update_compra, delete_compra, anular_compra
from app.ws import broadcast_multiple_sync

router = APIRouter()

@router.get("/", response_model=List[CompraResponse])
def read_compras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_compras(db, skip, limit)

@router.get("/{compra_id}", response_model=CompraResponse)
def read_compra(compra_id: int, db: Session = Depends(get_db)):
    db_compra = get_compra(db, compra_id)
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra not found")
    return db_compra

@router.post("/", response_model=CompraResponse)
def create_compra_endpoint(compra: CompraCreate, db: Session = Depends(get_db)):
    result = create_compra(db, compra, usuario_id=1)
    broadcast_multiple_sync(["compras", "dashboard", "reportes"], {"type": "created", "room": "compras"})
    return result

@router.put("/{compra_id}", response_model=CompraResponse)
def update_compra_endpoint(compra_id: int, compra: CompraUpdate, db: Session = Depends(get_db)):
    db_compra = update_compra(db, compra_id, compra)
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra not found")
    broadcast_multiple_sync(["compras", "dashboard", "reportes"], {"type": "updated", "room": "compras"})
    return db_compra

@router.put("/{compra_id}/anular", response_model=CompraResponse)
def anular_compra_endpoint(compra_id: int, db: Session = Depends(get_db)):
    result = anular_compra(db, compra_id)
    if not result:
        raise HTTPException(status_code=404, detail="Compra not found")
    broadcast_multiple_sync(["compras", "dashboard", "reportes"], {"type": "updated", "room": "compras"})
    return result

@router.delete("/{compra_id}")
def delete_compra_endpoint(compra_id: int, db: Session = Depends(get_db)):
    result = delete_compra(db, compra_id)
    if not result:
        raise HTTPException(status_code=404, detail="Compra not found")
    broadcast_multiple_sync(["compras", "dashboard", "reportes"], {"type": "deleted", "room": "compras"})
    return {"message": "Compra deleted"}

@router.get("/{compra_id}/pdf")
def compra_pdf(compra_id: int, db: Session = Depends(get_db)):
    try:
        from app.reports.compra_single import generar_comprobante_compra
        buffer = generar_comprobante_compra(db, compra_id)
        if not buffer:
            raise HTTPException(status_code=404, detail="Compra not found")
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=compra_{compra_id}.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
