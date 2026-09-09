from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.schemas.nota_entrega import NotaEntregaCreate, NotaEntregaResponse
from app.crud.nota_entrega import get_notas_entrega, get_nota_entrega, create_nota_entrega, delete_nota_entrega
from app.auth import get_current_user_full

router = APIRouter()

@router.get("/", response_model=List[NotaEntregaResponse])
def read_notas_entrega(
    venta_id: Optional[int] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_notas_entrega(db, venta_id=venta_id, skip=skip, limit=limit)

@router.get("/{nota_id}", response_model=NotaEntregaResponse)
def read_nota_entrega(nota_id: int, db: Session = Depends(get_db)):
    db_nota = get_nota_entrega(db, nota_id)
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota de entrega not found")
    return db_nota

@router.post("/", response_model=NotaEntregaResponse)
def create_nota_entrega_endpoint(nota: NotaEntregaCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user_full)):
    result = create_nota_entrega(db, nota, usuario_id=current_user.id)
    return result

@router.delete("/{nota_id}")
def delete_nota_entrega_endpoint(nota_id: int, db: Session = Depends(get_db)):
    result = delete_nota_entrega(db, nota_id)
    if not result:
        raise HTTPException(status_code=404, detail="Nota de entrega not found")
    return result

@router.get("/{nota_id}/pdf")
def descargar_pdf_nota_entrega(nota_id: int, db: Session = Depends(get_db)):
    try:
        from app.reports.nota_entrega_single import generar_pdf_nota_entrega
        buffer = generar_pdf_nota_entrega(db, nota_id)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Nota de entrega no encontrada")
        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=nota_entrega_{nota_id}.pdf'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
