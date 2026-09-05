from pydantic import BaseModel
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from app.schemas.producto_unidad import ProductoUnidadCreate, ProductoUnidadResponse

class ProductoBase(BaseModel):
    codigo: str
    categoria_id: int
    descripcion: str
    marca: str
    procedencia: str = ""
    precio: Decimal = 0
    utilidad: Decimal = 0
    stock_inicial: int
    stock_actual: int
    stock_minimo: int
    stock_maximo: int = 0
    imagen: Optional[str] = None
    usuario_id: int

class ProductoCreate(ProductoBase):
    unidades: Optional[List[ProductoUnidadCreate]] = None

class ProductoUpdate(BaseModel):
    categoria_id: Optional[int] = None
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    procedencia: Optional[str] = None
    precio: Optional[Decimal] = None
    utilidad: Optional[Decimal] = None
    stock_minimo: Optional[int] = None
    stock_maximo: Optional[int] = None
    imagen: Optional[str] = None
    activo: Optional[bool] = None
    unidades: Optional[List[ProductoUnidadCreate]] = None

class ProductoResponse(BaseModel):
    id: int
    codigo: str
    categoria_id: Optional[int] = None
    descripcion: str
    marca: str
    procedencia: str = ""
    precio: Decimal = 0
    utilidad: Decimal = 0
    stock_inicial: int
    stock_actual: int
    stock_minimo: int
    stock_maximo: int = 0
    imagen: Optional[str] = None
    usuario_id: Optional[int] = None
    activo: bool
    en_uso: bool = False
    fecha_registro: datetime
    fecha_actualizado: Optional[datetime] = None
    usuario_nombre: str = ""
    unidades: List[ProductoUnidadResponse] = []
    unidad_principal: Optional[ProductoUnidadResponse] = None

    model_config = {"from_attributes": True}
