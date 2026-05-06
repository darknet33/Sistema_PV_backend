from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Proveedor(BaseModel):
    __tablename__ = "proveedores"
    
    nombre = Column(String(100), nullable=False)
    nit = Column(String(20), nullable=False)
    materiales = Column(String(200), nullable=False)
    contacto = Column(String(100), nullable=False)
    celular_contacto = Column(String(20), nullable=False)
    email_contacto = Column(String(100), nullable=False)
    activo = Column(Boolean, default=True)
    
    compras = relationship("Compra", back_populates="proveedor")
