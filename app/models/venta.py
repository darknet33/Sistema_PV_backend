from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Venta(BaseModel):
    __tablename__ = "ventas"
    
    fecha = Column(DateTime, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id"))
    num_comprobante = Column(String(50))
    correlativo = Column(Boolean, default=0)
    estado_id = Column(Integer, ForeignKey("estados.id"))
    total = Column(DECIMAL(10, 2))
    impuesto = Column(DECIMAL(10, 2), default=0)
    it = Column(DECIMAL(10, 2), default=0)
    descuento = Column(DECIMAL(10, 2), default=0)
    activo = Column(Boolean, default=0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    cliente = relationship("Cliente", back_populates="ventas")
    comprobante = relationship("Comprobante", back_populates="ventas")
    estado = relationship("Estado", back_populates="ventas")
    usuario = relationship("Usuario", back_populates="ventas")
    detalles = relationship("VentaDetalle", back_populates="venta")
    notas_entrega = relationship("NotaEntrega", back_populates="venta")
