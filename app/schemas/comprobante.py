from pydantic import BaseModel
from typing import Optional

class ComprobanteBase(BaseModel):
    nombre: str
    numero: int = 1

class ComprobanteCreate(ComprobanteBase):
    pass

class ComprobanteResponse(ComprobanteBase):
    id: int
    
    class Config:
        from_attributes = True
