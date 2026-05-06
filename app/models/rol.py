from sqlalchemy import Column, String, Boolean,Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Rol(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    
    usuarios = relationship("Usuario", back_populates="rol")
    modulos = relationship("Modulo", secondary="rol_modulo", back_populates="roles")
