from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Usuario(BaseModel):
    __tablename__ = "usuarios"
    
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    cargo = Column(String(100), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True)
    
    rol = relationship("Rol", back_populates="usuarios")
    productos = relationship("Producto", back_populates="usuario")
    compras = relationship("Compra", back_populates="usuario")
    ventas = relationship("Venta", back_populates="usuario")
