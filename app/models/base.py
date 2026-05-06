from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_registro = Column(DateTime, default=func.now())
    fecha_actualizado = Column(DateTime, default=func.now(), onupdate=func.now())
