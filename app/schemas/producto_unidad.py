from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

class ProductoUnidadCreate(BaseModel):
    unidad_id: int
    es_principal: bool = False
    factor_conversion: Decimal = Field(default=Decimal("1"), ge=Decimal("0.0001"))

class ProductoUnidadResponse(BaseModel):
    id: int
    unidad_id: int
    unidad_nombre: str = ""
    unidad_abreviatura: str = ""
    es_principal: bool = False
    factor_conversion: Decimal = Decimal("1")

    class Config:
        from_attributes = True
