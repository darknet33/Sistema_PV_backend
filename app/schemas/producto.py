from pydantic import BaseModel, model_validator
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

class ProductoResponse(BaseModel):
    id: int
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
    activo: bool
    fecha_registro: datetime
    fecha_actualizado: Optional[datetime] = None
    usuario_nombre: str = ""
    
    class Config:
        from_attributes = True
    
    @model_validator(mode='before')
    @classmethod
    def set_usuario_nombre(cls, data):
        if hasattr(data, 'usuario') and data.usuario:
            data.usuario_nombre = f"{data.usuario.nombres} {data.usuario.apellidos}"
        elif isinstance(data, dict) and 'usuario' in data and data['usuario']:
            usuario = data['usuario']
            if hasattr(usuario, 'nombres'):
                data['usuario_nombre'] = f"{usuario.nombres} {usuario.apellidos}"
            else:
                data['usuario_nombre'] = f"{usuario.get('nombres', '')} {usuario.get('apellidos', '')}"
        return data
