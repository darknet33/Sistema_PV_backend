from sqlalchemy import Column, Integer, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base

class CompraDetalle(Base):
    __tablename__ = "detalles_compra"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    compra_id = Column(Integer, ForeignKey("compras.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    costo = Column(DECIMAL(10, 2), nullable=False)
    
    compra = relationship("Compra", back_populates="detalles")
    producto = relationship("Producto", back_populates="compras_detalle")
