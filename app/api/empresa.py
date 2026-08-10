from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
from pathlib import Path
from io import BytesIO
from PIL import Image
from app.database import get_db
from app.schemas.empresa import EmpresaUpdate, EmpresaResponse
from app.crud.empresa import get_empresa, update_empresa
from app.models.empresa import Empresa

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "empresa"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _default_response():
    return {
        "id": 1,
        "nombre": "",
        "razon_social": "",
        "nit": "",
        "telefono": "",
        "correo": "",
        "direccion": "",
        "ciudad": "",
        "logo": None,
        "color_principal": "#1677ff",
        "color_secundario": "#001529",
    }


@router.get("/", response_model=EmpresaResponse)
def read_empresa(db: Session = Depends(get_db)):
    db_empresa = get_empresa(db)
    if not db_empresa:
        return _default_response()
    return db_empresa


@router.put("/", response_model=EmpresaResponse)
def update_empresa_endpoint(data: EmpresaUpdate, db: Session = Depends(get_db)):
    return update_empresa(db, data)


@router.post("/logo")
async def upload_empresa_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_empresa = get_empresa(db)
    if not db_empresa:
        db_empresa = Empresa()
        db.add(db_empresa)
        db.flush()

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext or 'desconocido'}. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = UPLOAD_DIR / f"logo{ext}"

    contents = await file.read()
    try:
        img = Image.open(BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")

    image_path.write_bytes(contents)
    url = f"/uploads/empresa/logo{ext}"
    db_empresa.logo = url
    db.commit()
    db.refresh(db_empresa)
    return {"logo": url}


@router.delete("/logo", response_model=dict)
def delete_empresa_logo(db: Session = Depends(get_db)):
    db_empresa = get_empresa(db)
    if db_empresa and db_empresa.logo:
        try:
            old_path = Path(str(BASE_DIR / db_empresa.logo.lstrip("/")))
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass
        db_empresa.logo = None
        db.commit()
        db.refresh(db_empresa)
    return {"message": "Logo eliminado", "logo": None}
