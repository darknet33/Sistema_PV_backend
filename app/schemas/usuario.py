from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UsuarioBase(BaseModel):
    username: str
    nombres: str
    apellidos: str
    cargo: str
    rol_id: int

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    cargo: Optional[str] = None
    rol_id: Optional[int] = None
    password: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UsuarioAdminSetup(BaseModel):
    username: str
    password: str
    nombres: str
    apellidos: str

class UsuarioLogin(BaseModel):
    username: str
    password: str

class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    fecha_registro: datetime
    fecha_actualizado: datetime
    
    class Config:
        from_attributes = True
