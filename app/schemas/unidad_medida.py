from pydantic import BaseModel
from typing import Optional

class UnidadMedidaBase(BaseModel):
    nombre: str
    abreviatura: Optional[str] = None
    categoria_unidad_id: Optional[int] = None

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedidaResponse(UnidadMedidaBase):
    id: int
    activo: bool = True
    categoria_nombre: str = ""

    class Config:
        from_attributes = True
