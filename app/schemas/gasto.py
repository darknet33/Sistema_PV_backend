from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class GastoBase(BaseModel):
    fecha: datetime
    categoria_gasto_id: int
    descripcion: Optional[str] = None
    monto: Decimal
    estado_id: int

class GastoCreate(GastoBase):
    pass

class GastoUpdate(BaseModel):
    fecha: Optional[datetime] = None
    categoria_gasto_id: Optional[int] = None
    descripcion: Optional[str] = None
    monto: Optional[Decimal] = None
    estado_id: Optional[int] = None

class GastoResponse(BaseModel):
    id: int
    fecha: datetime
    categoria_gasto_id: int
    categoria_nombre: str = ""
    descripcion: Optional[str] = None
    monto: Decimal
    estado_id: int
    estado_nombre: str = ""
    activo: bool
    usuario_id: int
    usuario_username: str = ""
    fecha_registro: datetime

    class Config:
        from_attributes = True
