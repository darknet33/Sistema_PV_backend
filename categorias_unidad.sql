-- Datos existentes de la tabla categorias_unidad (sistema_yct)
-- Inserta solo registros que no existan (idempotente, respeta el id).
INSERT INTO categorias_unidad (id, nombre, descripcion, activo, fecha_registro, fecha_actualizado)
SELECT v.*
FROM (
  VALUES
    ROW(1,'PESO','Unidades de masa',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(2,'VOLUMEN','Unidades de volumen líquido',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(3,'LONGITUD','Unidades de longitud lineal',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(4,'SUPERFICIE','Unidades de área',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(5,'VOLUMEN CÚBICO','Unidades de volumen cúbico',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(6,'CANTIDAD','Unidades de conteo/empaque',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(7,'EMPAQUE/ENVASE','Envases y empaques',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(8,'FARMACÉUTICO','Unidades farmacéuticas',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(9,'ENERGÍA','Unidades de energía/potencia',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(10,'GAS NATURAL','Unidades de gas y volumen industrial',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(11,'TIEMPO','Unidades de tiempo',1,'2026-08-27 15:57:50','2026-08-27 15:57:50'),
    ROW(12,'OTROS','Otras unidades',1,'2026-08-27 15:57:50','2026-08-27 15:57:50')
) AS v(id, nombre, descripcion, activo, fecha_registro, fecha_actualizado)
WHERE NOT EXISTS (SELECT 1 FROM categorias_unidad c WHERE c.id = v.id);
