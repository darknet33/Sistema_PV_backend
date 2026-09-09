from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NotaEntregaDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int

class NotaEntregaDetalleResponse(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    producto_codigo: str
    producto_categoria: str
    cantidad: int

    class Config:
        from_attributes = True

class NotaEntregaCreate(BaseModel):
    venta_id: int
    fecha: Optional[datetime] = None
    entregue_nombre: str
    entregue_carnet: str
    recibi_nombre: str
    recibi_carnet: str
    detalles: List[NotaEntregaDetalleCreate]

class NotaEntregaResponse(BaseModel):
    id: int
    numero: str
    venta_id: int
    fecha: datetime
    entregue_nombre: str
    entregue_carnet: str
    recibi_nombre: str
    recibi_carnet: str
    usuario_id: int
    usuario_username: str = ""
    activo: bool
    total_cantidad: int
    fecha_registro: datetime
    detalles: List[NotaEntregaDetalleResponse]

    class Config:
        from_attributes = True
