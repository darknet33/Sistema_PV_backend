from sqlalchemy import Column, DateTime, Integer, Text, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Gasto(BaseModel):
    __tablename__ = "gastos"
    
    fecha = Column(DateTime, nullable=False)
    categoria_gasto_id = Column(Integer, ForeignKey("categorias_gastos.id"), nullable=False)
    descripcion = Column(Text)
    monto = Column(DECIMAL(10, 2), nullable=False)
    estado_id = Column(Integer, ForeignKey("estados.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    activo = Column(Boolean, default=1)
    
    categoria = relationship("CategoriaGasto", back_populates="gastos")
    estado = relationship("Estado")
    usuario = relationship("Usuario")
