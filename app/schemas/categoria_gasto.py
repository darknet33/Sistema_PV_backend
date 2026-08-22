from pydantic import BaseModel
from datetime import datetime

class CategoriaGastoBase(BaseModel):
    nombre: str

class CategoriaGastoCreate(CategoriaGastoBase):
    pass

class CategoriaGastoResponse(CategoriaGastoBase):
    id: int
    activo: bool
    fecha_registro: datetime
    
    class Config:
        from_attributes = True
