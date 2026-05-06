from pydantic import BaseModel
from typing import Optional

class EstadoBase(BaseModel):
    nombre: str

class EstadoCreate(EstadoBase):
    pass

class EstadoResponse(EstadoBase):
    id: int
    
    class Config:
        from_attributes = True
