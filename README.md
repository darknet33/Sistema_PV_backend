# Sistema RHINO - Backend API (FastAPI)

Backend completo para sistema de inventario desarrollado con FastAPI + SQLAlchemy + MySQL/MariaDB.

## Características
- **Autenticación JWT** con contraseñas hasheadas (bcrypt)
- **CRUD completo** para: Usuarios, Roles, Módulos, Categorías, Productos, Proveedores, Clientes, Comprobantes, Estados
- **Procesos de Compra y Venta** con actualización automática de stock
- **Reportes en PDF** (Kardex, Ventas, Compras) usando WeasyPrint
- **Exportación a Excel** con openpyxl
- **Validación con Pydantic v2**
- **Documentación automática** en `/docs` (Swagger UI)

## Instalación

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Configuración (.env)
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=rhino
DB_PASS=gyrx100PRE#
DB_NAME=SistemaRhino
JWT_SECRET=super-secret-key-change-in-production-2026
```

## Ejecución
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints
- POST `/api/auth/login` - Autenticación
- CRUD `/api/usuarios`, `/api/productos`, `/api/compras`, `/api/ventas`, etc.
- GET `/api/reportes/kardex/{id}` - Kardex PDF
- GET `/api/reportes/ventas/pdf` - Reporte ventas PDF
- GET `/api/reportes/compras/pdf` - Reporte compras PDF

## Base de Datos
Usar scripts en `run/SQL/` del proyecto original para crear la BD. Los triggers y procedimientos almacenados se mantienen.
