from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    nombre: str
    nit: str
    celular: str
    direccion: str

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: int
    activo: bool
    fecha_registro: datetime
    
    class Config:
        from_attributes = True
