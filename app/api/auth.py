from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.usuario import UsuarioLogin, UsuarioAdminSetup
from app.schemas.token import Token
from app.auth import authenticate_user, create_access_token, get_password_hash
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.modulo import Modulo
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
        db.commit()
        db.refresh(rol)

    for module_name in ADMIN_MODULES:
        modulo = db.query(Modulo).filter(Modulo.nombre == module_name).first()
        if not modulo:
            modulo = Modulo(nombre=module_name, activo=True)
            db.add(modulo)
            db.flush()
        if modulo not in rol.modulos:
            rol.modulos.append(modulo)
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
    return {
        "message": "Administrador creado exitosamente",
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/login", response_model=Token)
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
    return {"access_token": access_token, "token_type": "bearer"}
