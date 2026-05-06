from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Comprobante(Base):
    __tablename__ = "comprobantes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    numero = Column(Integer, default=1, nullable=False)
    
    compras = relationship("Compra", back_populates="comprobante")
    ventas = relationship("Venta", back_populates="comprobante")
