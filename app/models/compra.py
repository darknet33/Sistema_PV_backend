from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Compra(BaseModel):
    __tablename__ = "compras"
    
    fecha = Column(DateTime, nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id"))
    num_comprobante = Column(String(50))
    estado_id = Column(Integer, ForeignKey("estados.id"))
    total = Column(DECIMAL(10, 2))
    activo = Column(Integer, default=0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    proveedor = relationship("Proveedor", back_populates="compras")
    comprobante = relationship("Comprobante", back_populates="compras")
    estado = relationship("Estado", back_populates="compras")
    usuario = relationship("Usuario", back_populates="compras")
    detalles = relationship("CompraDetalle", back_populates="compra")
