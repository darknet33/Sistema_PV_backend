from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class VentaDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int
    precio: Decimal
    utilidad: Decimal = 0

class VentaDetalleResponse(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    producto_codigo: str
    producto_categoria: str
    cantidad: int
    precio: Decimal
    utilidad: Decimal

    class Config:
        from_attributes = True

class VentaBase(BaseModel):
    fecha: datetime
    cliente_id: int
    comprobante_id: int
    num_comprobante: Optional[str] = None
    estado_id: int
    impuesto: Decimal = 0
    descuento: Decimal = 0
    detalles: List[VentaDetalleCreate]

class VentaCreate(VentaBase):
    automatico: bool = True

class VentaUpdate(BaseModel):
    fecha: Optional[datetime] = None
    cliente_id: Optional[int] = None
    comprobante_id: Optional[int] = None
    num_comprobante: Optional[str] = None
    estado_id: Optional[int] = None
    impuesto: Optional[Decimal] = None
    descuento: Optional[Decimal] = None
    detalles: Optional[List[VentaDetalleCreate]] = None

class VentaResponse(BaseModel):
    id: int
    fecha: datetime
    cliente_id: int
    cliente_nombre: str
    comprobante_id: int
    comprobante_nombre: str
    num_comprobante: Optional[str] = None
    estado_id: int
    estado_nombre: str
    total: Decimal
    impuesto: Decimal
    descuento: Decimal
    activo: bool
    usuario_id: int
    usuario_username: str = ""
    usuario_nombre_completo: str = ""
    fecha_registro: datetime
    detalles: List[VentaDetalleResponse]

    class Config:
        from_attributes = True
