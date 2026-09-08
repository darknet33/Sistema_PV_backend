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


def _generar_derivados_logo(contents: bytes):
    """Genera favicon.ico y los íconos PWA (192/512) a partir del logo subido."""
    try:
        img = Image.open(BytesIO(contents)).convert("RGBA")

        icono = img.copy()
        icono.thumbnail((48, 48), Image.LANCZOS)
        icono.save(UPLOAD_DIR / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

        for size in (192, 512):
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            cuadrada = img.copy()
            cuadrada.thumbnail((size, size), Image.LANCZOS)
            offset = ((size - cuadrada.width) // 2, (size - cuadrada.height) // 2)
            canvas.paste(cuadrada, offset, cuadrada)
            canvas.save(UPLOAD_DIR / f"logo-{size}.png", format="PNG")
    except Exception:
        pass


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
        "imagen_encabezado": None,
        "imagen_pie": None,
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


async def _guardar_imagen(db: Session, file: UploadFile, prefijo: str, campo: str):
    """Valida la imagen, la guarda en uploads/empresa y actualiza el campo indicado."""
    db_empresa = get_empresa(db)
    if not db_empresa:
        db_empresa = Empresa()
        db.add(db_empresa)
        db.flush()

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext or 'desconocido'}. Permitidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = UPLOAD_DIR / f"{prefijo}{ext}"

    contents = await file.read()
    try:
        img = Image.open(BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")

    image_path.write_bytes(contents)
    url = f"/uploads/empresa/{prefijo}{ext}"
    setattr(db_empresa, campo, url)
    db.commit()
    db.refresh(db_empresa)

    if prefijo == "logo":
        _generar_derivados_logo(contents)

    return url


def _eliminar_imagen(db: Session, campo: str):
    db_empresa = get_empresa(db)
    url = getattr(db_empresa, campo) if db_empresa else None
    if db_empresa and url:
        try:
            old_path = Path(str(BASE_DIR / url.lstrip("/")))
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass
        if campo == "logo":
            for derivado in ("favicon.ico", "logo-192.png", "logo-512.png"):
                try:
                    derivado_path = UPLOAD_DIR / derivado
                    if derivado_path.exists():
                        derivado_path.unlink()
                except Exception:
                    pass
        setattr(db_empresa, campo, None)
        db.commit()
        db.refresh(db_empresa)
    return None


@router.post("/logo")
async def upload_empresa_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    url = await _guardar_imagen(db, file, "logo", "logo")
    return {"logo": url}


@router.delete("/logo", response_model=dict)
def delete_empresa_logo(db: Session = Depends(get_db)):
    _eliminar_imagen(db, "logo")
    return {"message": "Logo eliminado", "logo": None}


@router.post("/imagen-encabezado")
async def upload_empresa_imagen_encabezado(file: UploadFile = File(...), db: Session = Depends(get_db)):
    url = await _guardar_imagen(db, file, "encabezado", "imagen_encabezado")
    return {"imagen_encabezado": url}


@router.delete("/imagen-encabezado", response_model=dict)
def delete_empresa_imagen_encabezado(db: Session = Depends(get_db)):
    _eliminar_imagen(db, "imagen_encabezado")
    return {"message": "Imagen de encabezado eliminada", "imagen_encabezado": None}


@router.post("/imagen-pie")
async def upload_empresa_imagen_pie(file: UploadFile = File(...), db: Session = Depends(get_db)):
    url = await _guardar_imagen(db, file, "pie", "imagen_pie")
    return {"imagen_pie": url}


@router.delete("/imagen-pie", response_model=dict)
def delete_empresa_imagen_pie(db: Session = Depends(get_db)):
    _eliminar_imagen(db, "imagen_pie")
    return {"message": "Imagen de pie de página eliminada", "imagen_pie": None}
