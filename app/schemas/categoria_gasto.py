from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CategoriaGastoBase(BaseModel):
    nombre: str

class CategoriaGastoCreate(CategoriaGastoBase):
    pass

class CategoriaGastoResponse(CategoriaGastoBase):
    id: int
    activo: bool
    fecha_registro: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    
    class Config:
        from_attributes = True
