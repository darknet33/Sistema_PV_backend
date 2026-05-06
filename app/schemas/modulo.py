from pydantic import BaseModel
from typing import Optional

class ModuloBase(BaseModel):
    nombre: str
    activo: bool = True

class ModuloCreate(ModuloBase):
    pass

class ModuloResponse(ModuloBase):
    id: int
    
    class Config:
        from_attributes = True
