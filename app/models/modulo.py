from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Modulo(Base):
    __tablename__ = "modulos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    
    roles = relationship("Rol", secondary="rol_modulo", back_populates="modulos")
