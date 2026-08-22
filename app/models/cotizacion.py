from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Cotizacion(BaseModel):
    __tablename__ = "cotizaciones"

    numero = Column(String(20), unique=True, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    estado = Column(String(20), nullable=False, default="Enviado")
    con_factura = Column(Boolean, default=False)
    incluir_imagenes = Column(Boolean, default=False)
    modalidad_pago = Column(String(100), nullable=False, default="")
    forma_pago = Column(String(50), nullable=False, default="")
    validez_dias = Column(Integer, nullable=False, default=15)
    terminos_condiciones = Column(Text, nullable=False, default="")
    subtotal = Column(DECIMAL(10, 2), default=0)
    iva = Column(DECIMAL(10, 2), default=0)
    it = Column(DECIMAL(10, 2), default=0)
    descuento = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), default=0)
    activo = Column(Boolean, default=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    venta_id = Column(Integer, ForeignKey("ventas.id"), nullable=True)

    cliente_razon_social = Column(String(100), nullable=False, default="")
    cliente_nit = Column(String(20), nullable=False, default="")
    cliente_celular = Column(String(20), nullable=False, default="")
    cliente_direccion = Column(String(200), nullable=False, default="")

    cliente = relationship("Cliente", back_populates="cotizaciones")
    usuario = relationship("Usuario", back_populates="cotizaciones")
    venta = relationship("Venta")
    detalles = relationship("CotizacionDetalle", back_populates="cotizacion")
