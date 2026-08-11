from sqlalchemy import Column, String, Integer
from app.database import Base

class Empresa(Base):
    __tablename__ = "empresa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False, default="")
    razon_social = Column(String(150), nullable=False, default="")
    nit = Column(String(30), nullable=False, default="")
    telefono = Column(String(30), nullable=False, default="")
    correo = Column(String(120), nullable=False, default="")
    direccion = Column(String(200), nullable=False, default="")
    ciudad = Column(String(100), nullable=False, default="")
    logo = Column(String(255), nullable=True)
    imagen_encabezado = Column(String(255), nullable=True)
    imagen_pie = Column(String(255), nullable=True)
    color_principal = Column(String(9), nullable=False, default="#1677ff")
    color_secundario = Column(String(9), nullable=False, default="#001529")
