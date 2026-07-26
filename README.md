# Sistema de Inventario v3.0 — Backend

API REST para sistema de inventario POS.

## Stack

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Validación | Pydantic v2 |
| Base de Datos | MySQL (local) / PostgreSQL (producción) |
| Auth | JWT (python-jose + bcrypt) |
| PDF | Reportlab 4.2 |
| Excel | openpyxl |

## Requisitos

- Python 3.10+
- MySQL/MariaDB (local) o PostgreSQL (producción)

## Instalación

### 1. Base de Datos

**Local (MySQL):** Ejecutar scripts en orden desde `SQL/`:

```sql
SQL/1_schema_database.sql
SQL/2_tablas_basicas.sql
SQL/3_tablas_operacionales.sql
SQL/4_triggers.sql
SQL/5_procedures.sql
SQL/6_inserts_iniciales.sql
SQL/7_migraciones_extras.sql
```

**Producción (PostgreSQL):** Las tablas se crean automáticamente al iniciar el servidor.

### 2. Entorno

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
```

Configurar `.env` (local):

```env
DB_HOST=localhost
DB_PORT=3308
DB_USER=rhino
DB_PASS=gyrx100PRE#
DB_NAME=SistemaRhino
JWT_SECRET=super-secret-key-change-in-production-2026
```

### 3. Ejecutar

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Documentación automática en `http://localhost:8000/docs`

---

## Despliegue

### Render (Producción)

- **URL**: https://sistema-inventario-api-44kj.onrender.com
- **Rama**: `deploy`
- **Base de datos**: Supabase PostgreSQL (externa)
- **Configuración**: `render.yaml` + `Dockerfile`

### Variables de entorno en Render

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `JWT_SECRET` | Generado automáticamente |
| `JWT_ALGORITHM` | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 |

### Deploy manual

```bash
git checkout deploy
git push origin deploy
```

Render desplegará automáticamente al hacer push a `deploy`.

---

## Estructura

```
backend/
├── app/
│   ├── api/               # Endpoints REST
│   ├── auth/              # JWT
│   ├── crud/              # Lógica de negocio + BD
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Esquemas Pydantic
│   ├── reports/           # Generadores PDF
│   └── services/          # Consultas para reportes
├── SQL/                   # Scripts de BD
├── Dockerfile             # Configuración del contenedor
├── render.yaml            # Blueprint para Render
├── main.py
├── requirements.txt
└── .env
```

---

## Endpoints

| Ruta | Descripción |
|------|-------------|
| `POST /api/auth/login` | Autenticación |
| `POST /api/auth/setup-admin` | Configurar admin inicial |
| `GET /api/auth/check-users` | Verificar si hay usuarios |
| `GET /api/auth/me` | Usuario actual |
| `/api/usuarios` | CRUD usuarios |
| `/api/roles` | CRUD roles |
| `/api/modulos` | CRUD módulos |
| `/api/categorias` | CRUD + delete-all |
| `/api/productos` | CRUD + import/export Excel + soft-delete |
| `/api/proveedores` | CRUD + soft-delete |
| `/api/clientes` | CRUD clientes |
| `/api/comprobantes` | CRUD comprobantes |
| `/api/estados` | CRUD estados |
| `/api/compras` | CRUD + Anular + PDF |
| `/api/ventas` | CRUD + Anular + PDF + impuesto/descuento |
| `/api/reportes` | PDFs (Kardex, Ventas, Compras) |
| `ws /api/ws/{room}` | WebSocket (productos, ventas, compras, dashboard, reportes) |

---

## Convenciones

- **Moneda**: Bs. (Bolivianos)
- **Decimales**: Pydantic envía como string
- **N° Comprobante**: 8 dígitos, auto-generado con opción Manual
- **Anular**: revierte stock, requiere estado ANULADO para eliminar
- **Soft-Delete**: Proveedor/Producto usan `activo=False` si tienen relaciones
- **Stock**: Validación al crear/editar ventas
- **PDF**: Reportlab con `wordWrap='CJK'`, formato `Categoría - Descripción`
- **Dual DB**: `database.py` soporta MySQL (local) y PostgreSQL (producción) via `DATABASE_URL`
