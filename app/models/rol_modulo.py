from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class RolModulo(Base):
    __tablename__ = "rol_modulo"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rol_id = Column(Integer, ForeignKey("roles.id"))
    modulo_id = Column(Integer, ForeignKey("modulos.id"))
