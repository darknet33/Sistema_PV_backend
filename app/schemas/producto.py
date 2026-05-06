from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime

class ProductoBase(BaseModel):
    codigo: str
    categoria_id: int
    descripcion: str
    marca: str
    precio: Decimal = 0
    utilidad: Decimal = 0
    peso: Decimal = 0
    stock_inicial: int
    stock_actual: int
    stock_minimo: int
    usuario_id: int

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    categoria_id: Optional[int] = None
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    precio: Optional[Decimal] = None
    utilidad: Optional[Decimal] = None
    peso: Optional[Decimal] = None
    stock_minimo: Optional[int] = None
    activo: Optional[bool] = None

class ProductoResponse(ProductoBase):
    id: int
    activo: bool
    fecha_registro: datetime
    fecha_actualizado: datetime
    
    class Config:
        from_attributes = True
