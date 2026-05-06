from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class VentaDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int
    precio: Decimal
    utilidad: Decimal = 0

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
    pass

class VentaResponse(VentaBase):
    id: int
    total: Decimal
    activo: bool
    usuario_id: int
    fecha_registro: datetime
    
    class Config:
        from_attributes = True
