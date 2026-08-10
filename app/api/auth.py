from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.usuario import UsuarioLogin, UsuarioAdminSetup
from app.schemas.token import Token, LoginResponse
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.modulo import Modulo
from app.models.rol_modulo import RolModulo
from datetime import timedelta

router = APIRouter()

ADMIN_MODULES = [
    "Dashboard",
    "Productos",
    "Categorias",
    "Compras",
    "Ventas",
    "Clientes",
    "Proveedores",
    "Comprobantes",
    "Estados",
    "Reportes",
    "Usuarios",
    "Roles",
    "Empresa",
]

@router.get("/check-users")
async def check_users(db: Session = Depends(get_db)):
    users_count = db.query(Usuario).count()
    return {"has_users": users_count > 0, "needs_setup": users_count == 0}

@router.post("/setup-admin")
async def setup_admin(usuario: UsuarioAdminSetup, db: Session = Depends(get_db)):
    if db.query(Usuario).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existen usuarios en el sistema"
        )

    rol = db.query(Rol).filter(Rol.nombre == "ADMINISTRADOR").first()
    if not rol:
        rol = Rol(nombre="ADMINISTRADOR")
        db.add(rol)
        db.flush()

    created_module_ids = []
    for module_name in ADMIN_MODULES:
        modulo = db.query(Modulo).filter(Modulo.nombre == module_name).first()
        if not modulo:
            modulo = Modulo(nombre=module_name, activo=True)
            db.add(modulo)
            db.flush()
        created_module_ids.append(modulo.id)

        existe_asignacion = db.query(RolModulo).filter(
            RolModulo.rol_id == rol.id,
            RolModulo.modulo_id == modulo.id
        ).first()
        if not existe_asignacion:
            asignacion = RolModulo(rol_id=rol.id, modulo_id=modulo.id)
            db.add(asignacion)

    db.commit()
    db.refresh(rol)

    hashed_password = get_password_hash(usuario.password)
    new_user = Usuario(
        username=usuario.username,
        password=hashed_password,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        cargo="Administrador",
        rol_id=rol.id,
        activo=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )

    modulos = db.query(Modulo).filter(Modulo.id.in_(created_module_ids), Modulo.activo == True).all()

    return {
        "message": "Administrador creado exitosamente",
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": new_user.id,
            "username": new_user.username,
            "nombres": new_user.nombres,
            "apellidos": new_user.apellidos,
            "cargo": new_user.cargo,
            "rol_id": new_user.rol_id,
            "activo": new_user.activo,
        },
        "modulos": [{"id": m.id, "nombre": m.nombre} for m in modulos],
    }

@router.post("/login", response_model=LoginResponse)
async def login(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, usuario.username, usuario.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    modulos_asignados = db.query(RolModulo).filter(RolModulo.rol_id == user.rol_id).all()
    modulo_ids = [rm.modulo_id for rm in modulos_asignados]
    modulos = db.query(Modulo).filter(Modulo.id.in_(modulo_ids), Modulo.activo == True).all()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "username": user.username,
            "nombres": user.nombres,
            "apellidos": user.apellidos,
            "cargo": user.cargo,
            "rol_id": user.rol_id,
            "activo": user.activo,
        },
        "modulos": [{"id": m.id, "nombre": m.nombre} for m in modulos],
    }

@router.get("/me", response_model=LoginResponse)
async def get_me(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    modulos_asignados = db.query(RolModulo).filter(RolModulo.rol_id == current_user.rol_id).all()
    modulo_ids = [rm.modulo_id for rm in modulos_asignados]
    modulos = db.query(Modulo).filter(Modulo.id.in_(modulo_ids), Modulo.activo == True).all()

    return {
        "access_token": "",
        "token_type": "bearer",
        "usuario": {
            "id": current_user.id,
            "username": current_user.username,
            "nombres": current_user.nombres,
            "apellidos": current_user.apellidos,
            "cargo": current_user.cargo,
            "rol_id": current_user.rol_id,
            "activo": current_user.activo,
        },
        "modulos": [{"id": m.id, "nombre": m.nombre} for m in modulos],
    }
