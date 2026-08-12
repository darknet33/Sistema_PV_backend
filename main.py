import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import api_router
from app.database import init_db, Base
from app.models import Base
from app.ws import init_loop

init_db()

os.makedirs("uploads/productos", exist_ok=True)
os.makedirs("uploads/empresa", exist_ok=True)

app = FastAPI(
    title="Sistema YCT API",
    description="API para sistema de inventario con FastAPI",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup():
    init_loop(asyncio.get_running_loop())
    seed_empresa_module()
    seed_cotizaciones_module()


def _seed_module_por_nombre(db, nombre):
    from app.models.modulo import Modulo
    from app.models.rol import Rol
    from app.models.rol_modulo import RolModulo

    modulo = db.query(Modulo).filter(Modulo.nombre == nombre).first()
    if not modulo:
        modulo = Modulo(nombre=nombre, activo=True)
        db.add(modulo)
        db.flush()

    roles_destino = {rol_id for (rol_id,) in db.query(RolModulo.rol_id).distinct().all()}
    roles_admin = db.query(Rol.id).filter(Rol.nombre.ilike("%admin%")).all()
    roles_destino.update(rol_id for (rol_id,) in roles_admin)

    for rol_id in roles_destino:
        existente = db.query(RolModulo).filter(
            RolModulo.rol_id == rol_id,
            RolModulo.modulo_id == modulo.id
        ).first()
        if not existente:
            db.add(RolModulo(rol_id=rol_id, modulo_id=modulo.id))
    return modulo


def seed_empresa_module():
    try:
        from app.database import SessionLocal
        from app.models.modulo import Modulo
        from app.models.rol import Rol
        from app.models.rol_modulo import RolModulo

        db = SessionLocal()
        try:
            _seed_module_por_nombre(db, "Empresa")
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


def seed_cotizaciones_module():
    try:
        from app.database import SessionLocal
        from app.models.modulo import Modulo
        from app.models.rol import Rol
        from app.models.rol_modulo import RolModulo

        db = SessionLocal()
        try:
            _seed_module_por_nombre(db, "Cotizaciones")
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


@app.get("/")
def read_root():
    return {"message": "Sistema YCT API v3.0", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
