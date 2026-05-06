from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class CompraDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int
    costo: Decimal

class CompraBase(BaseModel):
    fecha: datetime
    proveedor_id: int
    comprobante_id: int
    num_comprobante: Optional[str] = None
    estado_id: int
    detalles: List[CompraDetalleCreate]

class CompraCreate(CompraBase):
    pass

class CompraResponse(CompraBase):
    id: int
    total: Decimal
    activo: bool
    usuario_id: int
    fecha_registro: datetime
    
    class Config:
        from_attributes = True
