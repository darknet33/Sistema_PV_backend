from sqlalchemy import Column, Integer, ForeignKey, Boolean, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ProductoUnidad(BaseModel):
    __tablename__ = "producto_unidades"
    __table_args__ = (
        UniqueConstraint("producto_id", "unidad_id", name="uq_producto_unidad"),
    )

    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    unidad_id = Column(Integer, ForeignKey("unidades_medida.id"), nullable=False)
    es_principal = Column(Boolean, default=False)
    factor_conversion = Column(DECIMAL(18, 4), nullable=False, default=1)

    producto = relationship("Producto", back_populates="unidades_producto")
    unidad = relationship("UnidadMedida", back_populates="producto_unidades")
