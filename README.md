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
| Migraciones | Alembic |

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

Para esquemas ya migrados con Alembic, las migraciones acumuladas en `alembic/versions/` son:

| Migración | Descripción |
|-----------|-------------|
| `6ccf96e83613` | Baseline del esquema actual |
| `df08dc1086a7` | Producto: procedencia, stock máximo/mínimo |
| `975c725d69a1` | Cotizaciones: tablas `cotizaciones` y `detalles_cotizacion` |
| `56d82524755d` | Empresa: imagen encabezado e imagen pie |

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
backend/
├── app/
│   ├── api/               # Routers (17 módulos)
│   ├── auth/              # JWT auth logic
│   ├── crud/              # Lógica de negocio + BD
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Esquemas Pydantic
│   ├── reports/           # Generadores PDF
│   ├── services/          # Consultas para reportes
│   └── utils/             # Excel, fechas
│   ├── database.py        # Conexión + get_db
│   └── ws.py              # ConnectionManager WebSocket
├── alembic/               # Migraciones
├── SQL/                   # Scripts de BD
├── uploads/               # Imágenes (productos/, empresa/)
├── main.py
├── requirements.txt
└── .env
```

---

## Endpoints

Prefijo general `/api` (definido en `app/api/__init__.py`).

### Auth (`/api/auth`)

| Ruta | Descripción |
|------|-------------|
| `POST /auth/login` | Login → `{ access_token, token_type, usuario, modulos }` |
| `GET /auth/me` | Usuario actual |
| `GET /auth/permisos` | Módulos asignados al rol del usuario |

### Configuración (`/api/configuracion`)

| Ruta | Descripción |
|------|-------------|
| `GET /configuracion/modulos` | Lista módulos con `activo` |
| `GET /configuracion/roles/{id}/modulos` | Módulos de un rol |
| `PUT /configuracion/roles/{id}/modulos` | Asigna módulos a un rol |

### Catálogos

| Ruta | Descripción |
|------|-------------|
| `/api/usuarios` | CRUD usuarios |
| `/api/roles` | CRUD roles |
| `/api/modulos` | CRUD módulos |
| `/api/categorias` | CRUD + delete-all (solo categorías sin productos asociados) |
| `/api/productos` | CRUD + imagen + Excel import/export + soft-delete (individual, batch, all) |
| `/api/proveedores` | CRUD + soft-delete |
| `/api/clientes` | CRUD clientes |
| `/api/comprobantes` | CRUD comprobantes |
| `/api/estados` | CRUD estados |

### Compras / Ventas (`/api/compras`, `/api/ventas`)

| Ruta | Descripción |
|------|-------------|
| `GET /` | Listar (orden por id DESC) |
| `GET /{id}` | Detalle con detalles anidados |
| `POST /` | Crear (valida FK, controla stock) |
| `PUT /{id}/anular` | Anular (revierte stock) |
| `GET /{id}/pdf` | PDF individual |
| `GET /{id}/pdf/preview` | Vista previa inline |

### Cotizaciones (`/api/cotizaciones`)

| Ruta | Descripción |
|------|-------------|
| `GET /` | Listar activas (ordena id DESC, paging skip/limit) |
| `GET /{cotizacion_id}` | Detalle con detalles anidados |
| `POST /` | Crear cotización (body `CotizacionCreate`) |
| `PUT /{cotizacion_id}` | Editar (solo estado `Enviado`, no convertidas) |
| `PUT /{cotizacion_id}/confirmar` | Pasar a `Confirmado` |
| `DELETE /{cotizacion_id}` | Soft-delete (`activo=False`; solo no confirmadas ni convertidas) |
| `POST /{cotizacion_id}/convertir-venta` | Convierte en venta (valida y descuenta stock) |
| `GET /{cotizacion_id}/pdf` | PDF descargable |
| `GET /{cotizacion_id}/pdf/preview` | Vista previa inline |

**Flujo de cotizaciones:**
- Estados automáticos: `Enviado` → `Confirmado` → convertida en venta (o `Vencido`).
- `_marcar_vencidas()`: al listar/obtener, toda cotización `Enviado` con `fecha_vencimiento < now` pasa a `Vencido`.
- Número auto-generado: `COT-{id:06d}` (p. ej. `COT-000042`).
- Fechas: el frontend envía solo fecha; el backend asigna hora actual (`datetime.combine(fecha.date(), datetime.now().time())`).
- Detalle: cada línea guarda `cantidad`, `costo`, `utilidad_pct` y `precio_venta` calculado = `costo + (costo * utilidad_pct / 100)` redondeado a 2 decimales.
- Totales: `subtotal = Σ cantidad * precio_venta`; `iva = subtotal * 16%` si `con_factura`; `descuento = subtotal * descuento%`; `total = subtotal + iva - descuento`.
- `validez_dias` por defecto 15 → `fecha_vencimiento = fecha + validez_dias`.
- `convertir-venta` (body `ConvertirVentaRequest`): solo cotizaciones `Confirmado` y sin `venta_id`. Valida stock (`_validar_stock_para_venta`), crea la `Venta` con `num_comprobante` auto (8 dígitos, con `with_for_update` en `Comprobante.numero`) o manual (`automatico=false`), descuenta stock por detalle (`_update_stock`), y enlaza `cotizacion.venta_id`. IVA 16% si `con_factura`. El descuento de la cotización se traslada a la venta. Crea el estado `Pendiente` si falta.
- Las respuestas incluyen `usuario_username`, datos del cliente (razón social, nit, celular, dirección) y producto (nombre, código, categoría, imagen).

### Reportes (`/api/reportes`)

| Ruta | Descripción |
|------|-------------|
| `GET /reportes/kardex/{producto_id}` | Kardex PDF |
| `GET /reportes/ventas/pdf` | Reporte ventas por rango (fecha_inicio/fin, cliente_text, estado) |
| `GET /reportes/compras/pdf` | Reporte compras por rango (fecha_inicio/fin, proveedor_text, estado) |

### Empresa (`/api/empresa`)

| Ruta | Descripción |
|------|-------------|
| `GET /` | Datos de la empresa (o por defecto si no existe) |
| `PUT /` | Actualizar datos + colores |
| `POST /logo` | Subir logo (multipart) |
| `DELETE /logo` | Eliminar logo |
| `POST /imagen-encabezado` | Subir imagen encabezado (PDFs) |
| `DELETE /imagen-encabezado` | Eliminar imagen encabezado |
| `POST /imagen-pie` | Subir imagen pie (PDFs) |
| `DELETE /imagen-pie` | Eliminar imagen pie |

- Guarda en `uploads/empresa/` con nombre fijo (`logo.png`, `encabezado.png`, `pie.png`) → mismo URL; el frontend maneja caché.
- Valida formato de imagen (`jpg/jpeg/png/gif/webp`) con Pillow.
- Los colores `color_principal`/`color_secundario` se usan en menú, login y PDFs.

### WebSocket (`/api/ws`)

- Endpoint: `ws://host/api/ws/{room}`
- Salas válidas: `productos`, `ventas`, `compras`, `dashboard`, `reportes`, `cotizaciones`
- Sin validación JWT (solo nombre de sala).
- Payload: `{"type": "created"|"updated"|"deleted", "room": "..."}`
- **Cotizaciones**: los endpoints broadcast a `["cotizaciones"]`.
- Broadcasts sincronos vía `broadcast_sync(room, data)` / `broadcast_multiple_sync(rooms, data)` (`loop.create_task()`).

---

## Convenciones

- **Moneda**: Bs. (Bolivianos)
- **Decimales**: Pydantic envía como string
- **N° Comprobante**: 8 dígitos, auto-generado con opción Manual (`automatico`); Manual NO incrementa `Comprobante.numero`
- **Anular**: revierte stock, requiere estado ANULADO para eliminar
- **Soft-Delete**: Proveedor/Producto usan `activo=False` si tienen relaciones; otros rechazan DELETE con 400. Batch y Delete-All también respetan esta regla.
- **Cotización soft-delete**: `activo=False` (no física); bloqueado si confirmada o convertida en venta.
- **Stock**: Validación de stock al crear/editar ventas — no permite vender más del stock disponible (cuenta con stock restaurado en ediciones)
- **PDF**: Reportlab con `wordWrap='CJK'`, formato `Categoría - Descripción`
- **PDF Venta (comprobante de venta)**: título = tipo de comprobante registrado (ej. `NOTA DE VENTA`); `N° de Comprobante` alineado a la derecha bajo el título; `Incluye IVA X%` solo si impuesto > 0; totales agrupados en bloque **Resumen** (SUBTOTAL, IVA, DESCUENTO, TOTAL)
- **PDF Cotización** (`reports/cotizacion_single.py`): encabezado con datos de empresa + logo, cliente, vigencia; tabla de detalle con 7 columnas (`#`, Código, Producto, Cant., Costo, P. Venta, Subtotal); muestra IVA solo si `con_factura`; pie con "Generado por" (nombre + apellidos del usuario).
