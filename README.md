# Sistema Rhino v3.0 — Backend

API REST para sistema de inventario POS.

## Stack

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Validación | Pydantic v2 |
| Base de Datos | MySQL/MariaDB (PyMySQL) |
| Auth | JWT (python-jose + bcrypt) |
| PDF | Reportlab 4.2 |
| Excel | openpyxl |

## Requisitos

- Python 3.10+
- MySQL/MariaDB

## Instalación

### 1. Base de Datos

Ejecutar scripts en orden desde `SQL/`:

```sql
SQL/1_schema_database.sql
SQL/2_tablas_basicas.sql
SQL/3_tablas_operacionales.sql
SQL/4_triggers.sql
SQL/5_procedures.sql
SQL/6_inserts_iniciales.sql
SQL/7_migraciones_extras.sql
```

### 2. Entorno

```bash
python -m venv venv
.\venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

Configurar `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
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

## Estructura

```
Sistema_PV_backend/
├── app/
│   ├── api/               # Endpoints REST
│   ├── auth/              # JWT
│   ├── crud/              # Lógica de negocio + BD
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Esquemas Pydantic
│   ├── reports/           # Generadores PDF
│   └── services/          # Consultas para reportes
├── SQL/                   # Scripts de BD
├── main.py
├── requirements.txt
└── .env
```

---

## Endpoints

| Ruta | Descripción |
|------|-------------|
| `POST /api/auth/login` | Autenticación |
| `/api/usuarios` | CRUD usuarios |
| `/api/roles` | CRUD roles |
| `/api/modulos` | CRUD módulos |
| `/api/categorias` | CRUD categorías |
| `/api/productos` | CRUD + import/export Excel |
| `/api/proveedores` | CRUD + soft-delete |
| `/api/clientes` | CRUD clientes |
| `/api/comprobantes` | CRUD comprobantes |
| `/api/estados` | CRUD estados |
| `/api/compras` | CRUD + Anular + PDF |
| `/api/ventas` | CRUD + Anular + PDF |
| `/api/reportes` | PDFs (Kardex, Ventas, Compras) |

---

## Convenciones

- **Moneda**: Bs. (Bolivianos)
- **Decimales**: Pydantic envía como string
- **N° Comprobante**: 8 dígitos, auto-generado con opción Manual
- **Anular**: revierte stock, requiere estado ANULADO para eliminar
- **Soft-Delete**: Proveedor/Producto usan `activo=False`; otros rechazan DELETE con 400
- **PDF**: Reportlab con `wordWrap='CJK'`, formato `Categoría - Descripción`
