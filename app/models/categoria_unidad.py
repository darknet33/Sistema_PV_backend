from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class CategoriaUnidad(BaseModel):
    __tablename__ = "categorias_unidad"

    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)

    unidades = relationship("UnidadMedida", back_populates="categoria")
