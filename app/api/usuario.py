from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, PasswordChange
from app.crud.usuario import (
    get_usuarios, get_usuario, create_usuario, update_usuario, delete_usuario, change_password
)
from app.auth import get_current_user_full, verify_password

router = APIRouter()

@router.get("/", response_model=List[UsuarioResponse])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_usuarios(db, skip, limit)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def read_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario

@router.post("/", response_model=UsuarioResponse)
def create_usuario_endpoint(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return create_usuario(db, usuario)

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario_endpoint(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = update_usuario(db, usuario_id, usuario)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario

@router.put("/{usuario_id}/password")
def cambiar_password(
    usuario_id: int,
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_full),
):
    if current_user.id != usuario_id:
        raise HTTPException(status_code=403, detail="Solo puede cambiar su propia contraseña")

    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")

    if not verify_password(payload.current_password, db_usuario.password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")

    change_password(db, usuario_id, payload.new_password)
    return {"message": "Contraseña actualizada correctamente"}

@router.delete("/{usuario_id}")
def delete_usuario_endpoint(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = delete_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return {"message": "Usuario deleted"}