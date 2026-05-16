from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class CompraDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int
    costo: Decimal

class CompraDetalleResponse(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    producto_codigo: str
    producto_categoria: str
    cantidad: int
    costo: Decimal

    class Config:
        from_attributes = True

class CompraBase(BaseModel):
    fecha: datetime
    proveedor_id: int
    comprobante_id: int
    num_comprobante: Optional[str] = None
    estado_id: int
    detalles: List[CompraDetalleCreate]

class CompraCreate(CompraBase):
    automatico: bool = True

class CompraUpdate(BaseModel):
    fecha: Optional[datetime] = None
    proveedor_id: Optional[int] = None
    comprobante_id: Optional[int] = None
    num_comprobante: Optional[str] = None
    estado_id: Optional[int] = None
    detalles: Optional[List[CompraDetalleCreate]] = None

class CompraResponse(BaseModel):
    id: int
    fecha: datetime
    proveedor_id: int
    proveedor_nombre: str
    comprobante_id: int
    comprobante_nombre: str
    num_comprobante: Optional[str] = None
    estado_id: int
    estado_nombre: str
    total: Decimal
    activo: bool
    usuario_id: int
    usuario_username: str = ""
    fecha_registro: datetime
    detalles: List[CompraDetalleResponse]

    class Config:
        from_attributes = True
