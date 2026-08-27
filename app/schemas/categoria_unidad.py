from pydantic import BaseModel
from typing import Optional

class CategoriaUnidadBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaUnidadCreate(CategoriaUnidadBase):
    pass

class CategoriaUnidadResponse(CategoriaUnidadBase):
    id: int
    activo: bool = True

    class Config:
        from_attributes = True
