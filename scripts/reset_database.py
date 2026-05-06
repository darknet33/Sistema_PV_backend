"""
Script para resetear la base de datos y hashear contraseñas
Ejecutar: cd backend && python scripts/reset_database.py
"""
import sys
import os

backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.auth import get_password_hash

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "rhino")
DB_PASS = os.getenv("DB_PASS", "gyrx100PRE#")
DB_NAME = os.getenv("DB_NAME", "SistemaRhino")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def reset_database():
    print("[INFO] Iniciando reset de base de datos...")
    
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Eliminar tablas
        print("[INFO] Eliminando tablas existentes...")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        result = db.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        
        for table in tables:
            db.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            print(f"[INFO] Eliminada: {table}")
        
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.commit()
        
        # 2. Ejecutar scripts SQL
        print("[INFO] Creando tablas desde scripts SQL...")
        
        sql_dir = os.path.join(backend_path, "..", "run", "SQL")
        sql_files = [
            "1_schema_database.sql",
            "2_tablas_basicas.sql", 
            "3_tablas_operacionales.sql",
            "4_triggers.sql",
            "5_procedures.sql",
            "6_inserts_iniciales.sql"
        ]
        
        for sql_file in sql_files:
            file_path = os.path.join(sql_dir, sql_file)
            if os.path.exists(file_path):
                print(f"[INFO] Ejecutando: {sql_file}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                statements = [s.strip() for s in content.split(';') if s.strip()]
                
                for stmt in statements:
                    if stmt and not stmt.startswith('DELIMITER'):
                        try:
                            db.execute(text(stmt))
                        except Exception as e:
                            print(f"[WARN] Error: {e}")
                db.commit()
        
        print("[OK] Tablas creadas")
        
        # 3. Hashear contraseñas
        print("[INFO] Actualizando contraseñas...")
        
        result = db.execute(text("SELECT id, username, password FROM usuarios"))
        usuarios = result.fetchall()
        
        if not usuarios:
            print("[WARN] No hay usuarios, creando admin...")
            
            result = db.execute(text("SELECT id FROM roles WHERE nombre = 'ADMIN'"))
            rol_row = result.first()
            
            if not rol_row:
                db.execute(text("INSERT INTO roles (nombre, descripcion) VALUES ('ADMIN', 'Administrador')"))
                db.commit()
                result = db.execute(text("SELECT id FROM roles WHERE nombre = 'ADMIN'"))
                rol_row = result.first()
            
            rol_id = rol_row[0]
            password_hash = get_password_hash("admin123")
            
            db.execute(
                text("INSERT INTO usuarios (username, password, nombres, apellidos, cargo, rol_id, activo) VALUES (:u, :p, :n, :a, :c, :r, :act)"),
                {"u": "admin", "p": password_hash, "n": "Administrador", "a": "Sistema", "c": "Administrador", "r": rol_id, "act": True}
            )
            print("[OK] Usuario admin creado - admin/admin123")
        else:
            for usr in usuarios:
                user_id = usr[0]
                username = usr[1]
                current_pwd = usr[2]
                
                if current_pwd and not current_pwd.startswith('$2b$'):
                    print(f"[INFO] Hasheando password de: {username}")
                    new_hash = get_password_hash(current_pwd)
                    db.execute(
                        text("UPDATE usuarios SET password = :h WHERE id = :id"),
                        {"h": new_hash, "id": user_id}
                    )
            
            print("[OK] Contraseñas actualizadas")
        
        db.commit()
        print("\n[OK] Reset completado!")
        print("\nCredenciales: admin / admin123")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
