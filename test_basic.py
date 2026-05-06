"""Test básico sin conexión a BD"""
import sys
print("Python version:", sys.version)
print()

# Test SQLAlchemy imports
try:
    from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DECIMAL
    print("✓ sqlalchemy imports OK")
except Exception as e:
    print(f"✗ sqlalchemy: {e}")

# Test DECIMAL
try:
    from sqlalchemy import DECIMAL
    print(f"✓ DECIMAL type: {DECIMAL}")
except Exception as e:
    print(f"✗ DECIMAL: {e}")

# Test model imports (without DB connection)
try:
    # No importamos database.py para evitar la conexión
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
    print("✓ Base model OK")
except Exception as e:
    print(f"✗ Base model: {e}")

print()
print("Test básico completado!")
print("Para test completo, instala dependencias con: pip install -r requirements.txt")
