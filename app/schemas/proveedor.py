from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProveedorBase(BaseModel):
    nombre: str
    nit: str
    materiales: str
    contacto: str
    celular_contacto: str
    email_contacto: str = ""

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorResponse(ProveedorBase):
    id: int
    activo: bool
    fecha_registro: datetime
    
    class Config:
        from_attributes = True
