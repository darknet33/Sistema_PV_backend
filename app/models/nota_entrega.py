from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel

class NotaEntrega(BaseModel):
    __tablename__ = "notas_entrega"

    numero = Column(String(20), unique=True, nullable=False)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    fecha = Column(DateTime, nullable=False)
    entregue_nombre = Column(String(100), nullable=False)
    entregue_carnet = Column(String(50), nullable=False)
    recibi_nombre = Column(String(100), nullable=False)
    recibi_carnet = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    activo = Column(Boolean, default=True)

    venta = relationship("Venta", back_populates="notas_entrega")
    usuario = relationship("Usuario", back_populates="notas_entrega")
    detalles = relationship("NotaEntregaDetalle", back_populates="nota_entrega", cascade="all, delete-orphan")

class NotaEntregaDetalle(Base):
    __tablename__ = "notas_entrega_detalle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_entrega_id = Column(Integer, ForeignKey("notas_entrega.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)

    nota_entrega = relationship("NotaEntrega", back_populates="detalles")
    producto = relationship("Producto", back_populates="notas_entrega_detalle")
