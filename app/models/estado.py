from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Estado(Base):
    __tablename__ = "estados"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    
    compras = relationship("Compra", back_populates="estado")
    ventas = relationship("Venta", back_populates="estado")
