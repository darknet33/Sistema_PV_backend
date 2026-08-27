from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UnidadMedida(BaseModel):
    __tablename__ = "unidades_medida"

    nombre = Column(String(100), unique=True, nullable=False)
    abreviatura = Column(String(20), nullable=True)
    categoria_unidad_id = Column(Integer, ForeignKey("categorias_unidad.id"))
    activo = Column(Boolean, default=True)

    categoria = relationship("CategoriaUnidad", back_populates="unidades")
    producto_unidades = relationship("ProductoUnidad", back_populates="unidad")
