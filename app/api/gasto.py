from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.schemas.gasto import GastoCreate, GastoUpdate, GastoResponse
from app.crud.gasto import get_gastos, get_gasto, create_gasto, update_gasto, anular_gasto, delete_gasto
from app.ws import broadcast_multiple_sync
from app.auth import get_current_user_full

router = APIRouter()

@router.get("/", response_model=List[GastoResponse])
def read_gastos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_gastos(db, skip, limit)

@router.get("/{gasto_id}", response_model=GastoResponse)
def read_gasto(gasto_id: int, db: Session = Depends(get_db)):
    db_gasto = get_gasto(db, gasto_id)
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto not found")
    return db_gasto

@router.post("/", response_model=GastoResponse)
def create_gasto_endpoint(gasto: GastoCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user_full)):
    result = create_gasto(db, gasto, usuario_id=current_user.id)
    broadcast_multiple_sync(["gastos", "dashboard", "reportes"], {"type": "created", "room": "gastos"})
    return result

@router.put("/{gasto_id}", response_model=GastoResponse)
def update_gasto_endpoint(gasto_id: int, gasto: GastoUpdate, db: Session = Depends(get_db)):
    db_gasto = update_gasto(db, gasto_id, gasto)
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto not found")
    broadcast_multiple_sync(["gastos", "dashboard", "reportes"], {"type": "updated", "room": "gastos"})
    return db_gasto

@router.put("/{gasto_id}/anular", response_model=GastoResponse)
def anular_gasto_endpoint(gasto_id: int, db: Session = Depends(get_db)):
    db_gasto = anular_gasto(db, gasto_id)
    if not db_gasto:
        raise HTTPException(status_code=404, detail="Gasto not found")
    broadcast_multiple_sync(["gastos", "dashboard", "reportes"], {"type": "updated", "room": "gastos"})
    return db_gasto

@router.delete("/{gasto_id}")
def delete_gasto_endpoint(gasto_id: int, db: Session = Depends(get_db)):
    result = delete_gasto(db, gasto_id)
    if not result:
        raise HTTPException(status_code=404, detail="Gasto not found")
    broadcast_multiple_sync(["gastos", "dashboard", "reportes"], {"type": "deleted", "room": "gastos"})
    return result
