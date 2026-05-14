# SistemaRhino - Scripts SQL Separados por Principios SOLID

Este paquete contiene los scripts SQL necesarios para configurar completamente la base de datos `SistemaRhino`. Los archivos están organizados para facilitar su lectura, mantenimiento y ejecución secuencial.

## Instrucciones de Ejecución

Ejecuta los archivos en el siguiente orden dentro de tu cliente SQL favorito (como DBeaver, MySQL Workbench o la consola de MariaDB):

### 1. Estructura Base
- `1_schema_database.sql`: Crea la base de datos y el usuario principal con todos los privilegios.

### 2. Tablas Básicas
- `2_tablas_basicas.sql`: Contiene las tablas fundamentales como `usuarios`, `roles`, `modulos`, `categorias`, etc.

### 3. Tablas Operacionales
- `3_tablas_operacionales.sql`: Define las tablas principales del flujo del sistema como `productos`, `compras`, `ventas`, `clientes`, etc.

### 4. Triggers
- `4_triggers.sql`: Incluye lógica automática como actualización de stock y cálculo de totales.

### 5. Procedures
- `5_procedures.sql`: Procedimientos almacenados para resumen de ventas, compras y movimientos de productos.

### 6. Datos Iniciales
- `6_inserts_iniciales.sql`: Población inicial con roles, estados, comprobantes, categorías, y algunos registros de prueba.

### 7. Alteraciones
- `7_alteraciones.sql`: Cualquier modificación adicional o mejora posterior a la creación de las tablas.

---

## Recomendaciones

- Verifica que el usuario `rhino` tenga los permisos adecuados antes de ejecutar los scripts operacionales.
- Asegúrate de tener habilitado el motor de almacenamiento InnoDB para soportar claves foráneas.
- Realiza respaldos periódicos si vas a hacer pruebas o desarrollos con estos scripts.

¡Buena implementación!
