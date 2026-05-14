# AGENTS.md — Contexto para Asistentes IA (Backend)

## Project Overview

**Sistema Rhino** v3.0 — Backend API REST para sistema de inventario POS. FastAPI + SQLAlchemy + MySQL/MariaDB.

### Stack
- FastAPI 0.115, SQLAlchemy 2.0, MySQL (PyMySQL), Pydantic v2
- JWT auth (python-jose + bcrypt)
- PDF: Reportlab 4.2
- Excel: openpyxl

---

## Project Structure

```
Sistema_PV_backend/
├── app/
│   ├── api/               # Route handlers (15 módulos)
│   ├── auth/              # JWT auth logic
│   ├── crud/              # DB operations (12 módulos)
│   ├── models/            # SQLAlchemy models (18 archivos)
│   ├── schemas/           # Pydantic schemas (13 archivos)
│   ├── reports/           # PDF generators (5 archivos)
│   └── services/          # Report data queries
├── SQL/                   # DB scripts (1..7 sequential)
├── main.py                # FastAPI entry point
├── requirements.txt
└── .env                   # DB config
```

---

## Architecture Conventions

### 3-layer pattern
```
api/ (routes) -> crud/ (business logic + DB) -> models/ (SQLAlchemy)
                            |
                      schemas/ (Pydantic validation)
```

All routers use prefix `/api` (defined in `app/api/__init__.py`).

### Naming
- snake_case, singular (`compra.py`, `producto.py`)
- CRUD files match API file names
- Model files match schema file names

---

## Key Patterns

### Auth
- JWT with 30min expiry
- `POST /api/auth/login` returns `{ access_token, token_type }`
- Routes protected via `Depends(get_current_user)`

### Compose Pattern (Compra/Venta CRUD)
- Master entity with inline detail rows
- `_validate_foreign_keys(db, ...)` validates all FKs exist before create/update
- `_update_stock(db, producto_id, cantidad, sumar)` — sumar=True adds, sumar=False subtracts
- `_build_response(db, entity)` builds dict with nested nombres (proveedor_nombre, cliente_nombre, etc.) and categoria
- `num_comprobante` auto-generated: 8-digit zero-padded from `Comprobante.numero` with `with_for_update` lock; `automatico: bool` controls behavior; Manual mode does NOT increment `Comprobante.numero`
- Date from frontend is date-only; backend assigns current time via `datetime.combine(fecha.date(), datetime.now().time())`
- **Venta**: total = `subtotal + (subtotal * impuesto/100) - (subtotal * descuento/100)`

### Anular (Compra/Venta)
- `PUT /api/{entity}s/{id}/anular` changes estado to "ANULADO" (auto-creates if missing via `_get_estado_anulado`)
- **Compra**: reverts stock (`stock_actual -= cantidad`)
- **Venta**: reverts stock (`stock_actual += cantidad`)
- Delete only allowed when entity is "ANULADO" (HTTP 400 otherwise)

### Soft-Delete Pattern
- Entities with `activo` field (Proveedor, Producto): set `activo=False` if has related records
- Entities without `activo` (Comprobante, Estado, Categoria): raise HTTP 400 if has related records

### PDF Reports
- Reportlab with `SimpleDocTemplate`, `Table`, `Paragraph` with `wordWrap='CJK'`
- Product column: `"Categoría - Descripción"`
- `colWidths` in inches (`from reportlab.lib.units import inch`)
- Monetary values: `Bs.` format
- Item number column (`#`) in single entity PDF
- Single venta PDF: includes SUBTOTAL, IMPUESTO%, DESCUENTO%, TOTAL rows

### Excel
- `GET /api/productos/export-xlsx` — descarga `productos.xlsx`
- `POST /api/productos/import-xlsx` — importa desde archivo Excel

### Error Handling
- FastAPI HTTPException with descriptive `detail`

---

## Critical Implementation Details

- **DB**: MySQL/MariaDB port 3306, user `rhino`, DB name `SistemaRhino`
- **Server**: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Currency**: Bs. (Bolivianos)
- **Decimal serialization**: Pydantic v2 sends Decimal as string by default
- **User ID**: Hardcoded as `1` in create endpoints (JWT auth pending full migration)
- **Compra/Venta ordering**: By `id DESC` (not by fecha)
- **Estado "ANULADO"**: Created automatically if missing; searched by name in uppercase
- **Compra PDF columns**: `#`, Código, Producto (Categoría - Descripción), Cant., Costo (Bs.), Subtotal (Bs.)
- **Venta PDF columns**: `#`, Código, Producto (Categoría - Descripción), Cant., Precio (Bs.), Subtotal (Bs.) + SUBTOTAL, IMPUESTO%, DESCUENTO%, TOTAL

---

## State of Development

### Completed
- Auth system (JWT login, module-based permissions)
- CRUD endpoints: Usuarios, Roles, Módulos, Categorías, Productos, Proveedores, Clientes, Comprobantes, Estados, Compras, Ventas
- Compras: Full CRUD with anular, PDF (single + range), soft-delete protection
- Ventas: Full CRUD with anular, PDF (single + range), soft-delete protection, impuesto/descuento
- Reports: Kardex PDF, Ventas PDF, Compras PDF
- Excel import/export for Productos

### Common Tasks
- Adding new entity: Create model → schema → CRUD → API → register in `__init__.py`
- Adding PDF: Create `reports/entity.py` with Reportlab, add endpoint in `api/entity.py` or `api/reporte.py`
- Adding filters in range reports: Add query params to endpoint, ILIKE filter in report generator
