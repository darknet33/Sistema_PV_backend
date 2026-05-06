import sys
import subprocess

print("Verificando configuración del backend...")
print()

# Verificar Python
print(f"Python version: {sys.version}")
print()

# Verificar instalación de paquetes
packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pymysql', 'jose', 'bcrypt', 'dotenv', 'weasyprint', 'openpyxl', 'pydantic']

for package in packages:
    try:
        if package == 'jose':
            import jose
        elif package == 'dotenv':
            import dotenv
        else:
            __import__(package)
        print(f"✓ {package} instalado")
    except ImportError:
        print(f"✗ {package} NO instalado")

print()
print("Verificando imports del proyecto...")

try:
    from app.database import engine, Base, get_db
    print("✓ app.database")
except Exception as e:
    print(f"✗ app.database: {e}")

try:
    from app.models import Base
    print("✓ app.models")
except Exception as e:
    print(f"✗ app.models: {e}")

try:
    from app.schemas import UsuarioCreate, ProductoCreate
    print("✓ app.schemas")
except Exception as e:
    print(f"✗ app.schemas: {e}")

try:
    from app.crud import get_usuario, get_producto
    print("✓ app.crud")
except Exception as e:
    print(f"✗ app.crud: {e}")

try:
    from app.api import api_router
    print("✓ app.api")
except Exception as e:
    print(f"✗ app.api: {e}")

try:
    from app.auth import create_access_token
    print("✓ app.auth")
except Exception as e:
    print(f"✗ app.auth: {e}")

print()
print("Configuración completada!")
