from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class CotizacionDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(ge=1)
    costo: Decimal = Field(ge=0)
    utilidad_pct: Decimal = Field(default=0, ge=0)

class CotizacionDetalleResponse(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    producto_codigo: str
    producto_categoria: str
    producto_imagen: Optional[str] = None
    cantidad: int
    costo: Decimal
    utilidad_pct: Decimal
    precio_venta: Decimal

    class Config:
        from_attributes = True

class CotizacionBase(BaseModel):
    fecha: datetime
    cliente_id: int
    con_factura: bool = False
    incluir_imagenes: bool = False
    modalidad_pago: str = ""
    validez_dias: int = Field(default=15, ge=1)
    terminos_condiciones: str = ""
    detalles: List[CotizacionDetalleCreate]

class CotizacionCreate(CotizacionBase):
    pass

class CotizacionUpdate(BaseModel):
    fecha: Optional[datetime] = None
    cliente_id: Optional[int] = None
    con_factura: Optional[bool] = None
    incluir_imagenes: Optional[bool] = None
    modalidad_pago: Optional[str] = None
    validez_dias: Optional[int] = Field(default=None, ge=1)
    terminos_condiciones: Optional[str] = None
    detalles: Optional[List[CotizacionDetalleCreate]] = None

class CotizacionResponse(BaseModel):
    id: int
    numero: str
    fecha: datetime
    fecha_vencimiento: datetime
    cliente_id: int
    cliente_razon_social: str
    cliente_nit: str
    cliente_celular: str
    cliente_direccion: str
    estado: str
    con_factura: bool
    incluir_imagenes: bool
    modalidad_pago: str
    validez_dias: int
    terminos_condiciones: str
    subtotal: Decimal
    iva: Decimal
    total: Decimal
    activo: bool
    usuario_id: int
    usuario_username: str = ""
    venta_id: Optional[int] = None
    fecha_registro: datetime
    detalles: List[CotizacionDetalleResponse]

    class Config:
        from_attributes = True

class ConvertirVentaRequest(BaseModel):
    comprobante_id: int
    estado_id: Optional[int] = None
    num_comprobante: Optional[str] = None
    automatico: bool = True
