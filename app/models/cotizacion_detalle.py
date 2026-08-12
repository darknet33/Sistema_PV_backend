from sqlalchemy import Column, Integer, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base

class CotizacionDetalle(Base):
    __tablename__ = "detalles_cotizacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    costo = Column(DECIMAL(10, 2), nullable=False, default=0)
    utilidad_pct = Column(DECIMAL(10, 2), nullable=False, default=0)
    precio_venta = Column(DECIMAL(10, 2), nullable=False, default=0)

    cotizacion = relationship("Cotizacion", back_populates="detalles")
    producto = relationship("Producto", back_populates="cotizaciones_detalle")
