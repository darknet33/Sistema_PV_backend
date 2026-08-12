from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Cliente(BaseModel):
    __tablename__ = "clientes"
    
    nombre = Column(String(100), nullable=False)
    nit = Column(String(20), nullable=False)
    celular = Column(String(20), nullable=False)
    direccion = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)
    
    ventas = relationship("Venta", back_populates="cliente")
    cotizaciones = relationship("Cotizacion", back_populates="cliente")
