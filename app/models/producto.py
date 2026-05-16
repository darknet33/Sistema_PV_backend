from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Producto(BaseModel):
    __tablename__ = "productos"
    
    codigo = Column(String(50), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    descripcion = Column(Text, nullable=False)
    marca = Column(String(50), nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False, default=0)
    utilidad = Column(DECIMAL(10, 2), nullable=False, default=0)
    peso = Column(DECIMAL(10, 2), nullable=False, default=0)
    stock_inicial = Column(Integer, nullable=False)
    stock_actual = Column(Integer, nullable=False)
    stock_minimo = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    categoria = relationship("Categoria", back_populates="productos")
    usuario = relationship("Usuario", back_populates="productos")
    compras_detalle = relationship("CompraDetalle", back_populates="producto")
    ventas_detalle = relationship("VentaDetalle", back_populates="producto")
    
    @property
    def usuario_nombre(self):
        if self.usuario:
            return self.usuario.username
        return ""
