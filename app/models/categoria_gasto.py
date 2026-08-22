from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class CategoriaGasto(BaseModel):
    __tablename__ = "categorias_gastos"
    
    nombre = Column(String(100), unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    
    gastos = relationship("Gasto", back_populates="categoria")
