from sqlalchemy import Column, Integer, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base

class VentaDetalle(Base):
    __tablename__ = "detalles_venta"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    utilidad = Column(DECIMAL(10, 2), nullable=False, default=0)
    
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="ventas_detalle")
