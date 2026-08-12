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
- `_validar_stock_para_venta(db, detalles, old_detalles=None)` — validates stock before creating/updating a Venta; raises HTTP 400 if any product has insufficient stock. For updates, `old_detalles` stock is accounted for (restored first).
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
  - **Individual delete** (`DELETE /productos/{id}`): checks relations; soft-delete if has, hard-delete otherwise
  - **Batch delete** (`POST /productos/delete-batch`): same per-product logic as individual
  - **Delete all** (`DELETE /productos/all`): same per-product logic — soft-deletes those with relations, hard-deletes those without
- Entities without `activo` (Categoria, Comprobante, Estado): raise HTTP 400 if has related records
  - **Delete all** for Categoria (`DELETE /categorias/all`): hard-deletes categories without products, skips those with products (reports which were omitted)

### PDF Reports
- Reportlab with `SimpleDocTemplate`, `Table`, `Paragraph` with `wordWrap='CJK'`
- Product column: `"Categoría - Descripción"`
- `colWidths` in inches (`from reportlab.lib.units import inch`)
- Monetary values: `Bs.` format
- Item number column (`#`) in single entity PDF
- **Venta PDF (comprobante de venta)** — `reports/venta_single.py`:
  - Título dinámico con el tipo de comprobante registrado (ej. `NOTA DE VENTA`); fallback `Comprobante de Venta`
  - `N° de Comprobante` mostrado de forma separada y discreta: alineado a la derecha bajo el título, negrita tamaño ~13 (`venta.num_comprobante`, fallback `venta.id`)
  - En los datos solo aparece `Incluye IVA X%` si `impuesto > 0` (oculto si es 0)
  - Los totales van en un bloque separado **Resumen** alineado a la derecha: SUBTOTAL, IVA (X%) solo si > 0, DESCUENTO (X%) solo si > 0 y TOTAL resaltado con el color secundario de la empresa

### WebSocket
- Endpoint: `ws://host/api/ws/{room}` at `app/api/ws.py`
- Rooms: `productos`, `ventas`, `compras`, `dashboard`, `reportes`
- ConnectionManager singleton at `app/ws.py` with `connect()`, `disconnect()`, `broadcast()`
- Broadcast helpers `broadcast_sync(room, data)` and `broadcast_multiple_sync(rooms, data)` for sync endpoints via `loop.create_task()`
- **Producto** endpoints broadcast to `["productos", "dashboard"]`
- **Compra** endpoints broadcast to `["compras", "dashboard", "reportes"]`
- **Venta** endpoints broadcast to `["ventas", "dashboard", "reportes"]`
- Message payload: `{"type": "created"|"updated"|"deleted", "room": "..."}`
- No JWT validation on WebSocket (only room name validated)

### Excel
- `GET /api/productos/export-xlsx` — descarga `productos.xlsx`
- `POST /api/productos/import-xlsx` — importa desde archivo Excel
- **Columnas**: `ÏD`, `Código`, `Categoría`, `Descripción`, `Marca`, `Procedencia`, `Costo Bs.`, `Utilidad Bs.`, `Stock Inicial`, `Stock Mínimo`, `Stock Máximo`, `Estado`
- `Costo Bs.` se mapea a `precio` en la BD; `Stock Actual` no se importa (se gestiona automáticamente, arranca en 0 para nuevos productos)

### Migraciones (Alembic)
- Configuración en `alembic/env.py` (lee `DATABASE_URL` de `app.database`, `target_metadata = Base.metadata` con `import app.models`)
- Crear migración: `venv\Scripts\alembic.exe revision --autogenerate -m "<descripcion>"`
- Aplicar: `venv\Scripts\alembic.exe upgrade head`
- Baseline inicial (no-op) = `6ccf96e83613`; cambios de producto = `df08dc1086a7`

### Imagen de Producto
- `POST /api/productos/{id}/imagen` (multipart) — valida formato (`jpg/jpeg/png/gif/webp`) y que sea imagen válida (Pillow); guarda en `uploads/productos/{id}{ext}` y devuelve `{ "imagen": "/uploads/productos/{id}{ext}" }`
- `DELETE /api/productos/{id}/imagen` — elimina archivo y pone `imagen = NULL`
- Estáticos montados en `/uploads` (main.py), carpetas creadas en `main.py` al importar

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
- **Usuario**: Producto, Compra y Venta responses incluyen `usuario_username` (username del usuario que registró)
- **Compra PDF columns**: `#`, Código, Producto (Categoría - Descripción), Cant., Costo (Bs.), Subtotal (Bs.)
- **Venta PDF columns**: `#`, Código, Producto (Categoría - Descripción), Cant., Precio (Bs.), Subtotal (Bs.) — los totales NO van en la tabla; se agrupan en el bloque `Resumen` (SUBTOTAL / IVA (X%) / DESCUENTO (X%) / TOTAL)

---

## State of Development

### Completed
- Auth system (JWT login, module-based permissions)
- CRUD endpoints: Usuarios, Roles, Módulos, Categorías, Productos, Proveedores, Clientes, Comprobantes, Estados, Compras, Ventas
- Compras: Full CRUD with anular, PDF (single + range), soft-delete protection
- Ventas: Full CRUD with anular, PDF (single + range), soft-delete protection, impuesto/descuento
- Reports: Kardex PDF, Ventas PDF, Compras PDF
- Venta PDF rediseñado: título con tipo de comprobante, N° de comprobante discreto/destacado, "Incluye IVA X%" condicional y totales agrupados en bloque `Resumen`
- Excel import/export for Productos
- Productos soft-delete: individual, batch, and delete-all all use `_tiene_relaciones()` helper to decide soft vs hard delete

### Common Tasks
- Adding new entity: Create model → schema → CRUD → API → register in `__init__.py`
- Adding PDF: Create `reports/entity.py` with Reportlab, add endpoint in `api/entity.py` or `api/reporte.py`
- Adding filters in range reports: Add query params to endpoint, ILIKE filter in report generator
