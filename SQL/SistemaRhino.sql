-- ================================================
-- SistemaRhino_MariaDB.sql
-- Script completo para MariaDB
-- Incluye: Estructura, triggers e inserts
-- ================================================

CREATE DATABASE IF NOT EXISTS SistemaRhino CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE SistemaRhino;

-- Crear el usuario rhino@% con todos los privilegios para esta base de datos
CREATE USER IF NOT EXISTS 'rhino'@'%' IDENTIFIED BY 'gyrx100PRE#';
GRANT ALL PRIVILEGES ON SistemaRhino.* TO 'rhino'@'%';
FLUSH PRIVILEGES;

-- ================================================
-- TABLAS
-- ================================================

CREATE TABLE roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE modulos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  activo TINYINT(1) DEFAULT 1
);

CREATE TABLE rol_modulo (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rol_id INT,
  modulo_id INT,
  FOREIGN KEY (rol_id) REFERENCES roles(id),
  FOREIGN KEY (modulo_id) REFERENCES modulos(id)
);

CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  nombres VARCHAR(100) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  cargo VARCHAR(100) NOT NULL,
  rol_id INT NOT NULL,
  fecha_registro DATETIME DEFAULT NOW(),
  fecha_actualizado DATETIME DEFAULT NOW() ON UPDATE NOW(),
  activo TINYINT(1) DEFAULT 1,
  FOREIGN KEY (rol_id) REFERENCES roles(id)
);

CREATE TABLE categorias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL
);

CREATE TABLE productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(50) NOT NULL,
  categoria_id INT,
  descripcion TEXT NOT NULL,
  marca VARCHAR(50) NOT NULL,
  precio DECIMAL(10,2) NOT null,
  peso DECIMAL(10,2) NOT null,
  stock_inicial INT NOT NULL,
  stock_actual INT NOT NULL,
  stock_minimo INT NOT NULL,
  fecha_registro DATETIME DEFAULT NOW(),
  fecha_actualizado DATETIME DEFAULT NOW() ON UPDATE NOW(),
  activo TINYINT(1) DEFAULT 1,
  usuario_id INT,
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE comprobantes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  numero INT DEFAULT 1 NOT NULL
);

CREATE TABLE estados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL
);

CREATE TABLE transacciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL
);

CREATE TABLE proveedores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  nit VARCHAR(20) NOT NULL,
  materiales VARCHAR(200) NOT NULL,
  contacto VARCHAR(100) NOT NULL,
  celular_contacto VARCHAR(20) NOT NULL,
  email_contacto VARCHAR(100) NOT NULL,
  activo TINYINT(1) DEFAULT 1,
  fecha_registro DATETIME DEFAULT NOW()
);

CREATE TABLE compras (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME NOT NULL,
  proveedor_id INT,
  comprobante_id INT,
  num_comprobante VARCHAR(50),
  estado_id INT,
  total DECIMAL(10,2),
  usuario_id INT,
  FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
  FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id),
  FOREIGN KEY (estado_id) REFERENCES estados(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE detalles_compra (
  id INT AUTO_INCREMENT PRIMARY KEY,
  compra_id INT,
  producto_id INT,
  cantidad INT NOT NULL,
  costo DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (compra_id) REFERENCES compras(id),
  FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  nit VARCHAR(20) NOT NULL,
  celular VARCHAR(20) NOT NULL,
  direccion TEXT NOT NULL,
  activo TINYINT(1) DEFAULT 1,
  fecha_registro DATETIME DEFAULT NOW()
);

CREATE TABLE ventas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME NOT NULL,
  cliente_id INT,
  comprobante_id INT,
  num_comprobante VARCHAR(50),
  estado_id INT,
  total DECIMAL(10,2),
  impuesto DECIMAL(10,2),
  descuento DECIMAL(10,2),
  usuario_id INT,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id),
  FOREIGN KEY (estado_id) REFERENCES estados(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE detalles_venta (
  id INT AUTO_INCREMENT PRIMARY KEY,
  venta_id INT,
  producto_id INT,
  cantidad INT NOT NULL,
  precio DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (venta_id) REFERENCES ventas(id),
  FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS categorias_gastos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  activo TINYINT(1) DEFAULT 1,
  fecha_registro DATETIME DEFAULT NOW(),
  fecha_actualizado DATETIME DEFAULT NOW() ON UPDATE NOW()
);

CREATE TABLE IF NOT EXISTS gastos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME NOT NULL,
  categoria_gasto_id INT NOT NULL,
  descripcion TEXT,
  monto DECIMAL(10,2) NOT NULL,
  estado_id INT,
  usuario_id INT,
  activo TINYINT(1) DEFAULT 1,
  fecha_registro DATETIME DEFAULT NOW(),
  fecha_actualizado DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (categoria_gasto_id) REFERENCES categorias_gastos(id),
  FOREIGN KEY (estado_id) REFERENCES estados(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ================================================
-- TRIGGERS
-- ================================================

DELIMITER $$
CREATE TRIGGER tr_insertar_detalle_venta AFTER INSERT ON detalles_venta FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual - NEW.cantidad WHERE id = NEW.producto_id;
  UPDATE ventas SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = NEW.venta_id) WHERE id = NEW.venta_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER tr_actualizar_detalle_venta AFTER UPDATE ON detalles_venta FOR EACH ROW
BEGIN
  IF OLD.producto_id = NEW.producto_id THEN
    UPDATE productos SET stock_actual = stock_actual + OLD.cantidad - NEW.cantidad WHERE id = NEW.producto_id;
  ELSE
    UPDATE productos SET stock_actual = stock_actual + OLD.cantidad WHERE id = OLD.producto_id;
    UPDATE productos SET stock_actual = stock_actual - NEW.cantidad WHERE id = NEW.producto_id;
  END IF;
  UPDATE ventas SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = NEW.venta_id) WHERE id = NEW.venta_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER tr_borrar_detalle_venta AFTER DELETE ON detalles_venta FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual + OLD.cantidad WHERE id = OLD.producto_id;
  UPDATE ventas SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = OLD.venta_id) WHERE id = OLD.venta_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER tr_insertar_detalle_compra AFTER INSERT ON detalles_compra FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual + NEW.cantidad WHERE id = NEW.producto_id;
  UPDATE compras SET total = (SELECT IFNULL(SUM(cantidad * costo), 0) FROM detalles_compra WHERE compra_id = NEW.compra_id) WHERE id = NEW.compra_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER tr_actualizar_detalle_compra AFTER UPDATE ON detalles_compra FOR EACH ROW
BEGIN
  IF OLD.producto_id = NEW.producto_id THEN
    UPDATE productos SET stock_actual = stock_actual - OLD.cantidad + NEW.cantidad WHERE id = NEW.producto_id;
  ELSE
    UPDATE productos SET stock_actual = stock_actual - OLD.cantidad WHERE id = OLD.producto_id;
    UPDATE productos SET stock_actual = stock_actual + NEW.cantidad WHERE id = NEW.producto_id;
  END IF;
  UPDATE compras SET total = (SELECT IFNULL(SUM(cantidad * costo), 0) FROM detalles_compra WHERE compra_id = NEW.compra_id) WHERE id = NEW.compra_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER tr_borrar_detalle_compra AFTER DELETE ON detalles_compra FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual - OLD.cantidad WHERE id = OLD.producto_id;
  UPDATE compras SET total = (SELECT IFNULL(SUM(cantidad * costo), 0) FROM detalles_compra WHERE compra_id = OLD.compra_id) WHERE id = OLD.compra_id;
END $$
DELIMITER ;


-- ================================================
-- PROCEDURE STORAGE
-- ================================================

DELIMITER //

CREATE PROCEDURE kardex_producto (
    IN p_producto_id INT,
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    SELECT 
        m.fecha,
        m.tipo,
        m.detalle,
        m.cantidad
    FROM (
        SELECT 
            c.fecha,
            'ENTRADA' AS tipo,
            CONCAT('Compra #', c.id) AS detalle,
            dc.cantidad
        FROM compras c
        JOIN detalles_compra dc ON dc.compra_id = c.id
        WHERE dc.producto_id = p_producto_id

        UNION ALL

        SELECT 
            v.fecha,
            'SALIDA' AS tipo,
            CONCAT('Venta #', v.id) AS detalle,
            -dv.cantidad
        FROM ventas v
        JOIN detalles_venta dv ON dv.venta_id = v.id
        WHERE dv.producto_id = p_producto_id
    ) m
    WHERE m.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
    ORDER BY m.fecha;
END //

DELIMITER ;


DROP PROCEDURE IF EXISTS kardex_con_saldo;

DELIMITER //

CREATE PROCEDURE kardex_con_saldo (
    IN p_producto_id INT,
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    -- Variables de control
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_fecha DATETIME;
    DECLARE v_tipo VARCHAR(20);
    DECLARE v_detalle VARCHAR(200);
    DECLARE v_cantidad INT;
    DECLARE v_saldo INT;
    DECLARE v_fecha_registro DATETIME;

 -- Cursor para movimientos dentro del rango
DECLARE cur CURSOR FOR 
    SELECT DATE(fecha) AS fecha, tipo, detalle, cantidad
    FROM (
        -- Entradas (compras)
        SELECT 
            c.fecha,
            'ENTRADA' AS tipo,
            CONCAT('Compra - ', comp.nombre, ' N° ', c.num_comprobante, ' (ID: ', c.id, ')') AS detalle,
            dc.cantidad
        FROM compras c
        JOIN detalles_compra dc ON dc.compra_id = c.id
        JOIN comprobantes comp ON comp.id = c.comprobante_id
        WHERE dc.producto_id = p_producto_id
          AND c.fecha BETWEEN p_fecha_inicio AND p_fecha_fin

        UNION ALL

        -- Salidas (ventas)
        SELECT 
            v.fecha,
            'SALIDA' AS tipo,
            CONCAT('Venta - ', comp.nombre, ' N° ', v.num_comprobante, ' (ID: ', v.id, ')') AS detalle,
            -dv.cantidad
        FROM ventas v
        JOIN detalles_venta dv ON dv.venta_id = v.id
        JOIN comprobantes comp ON comp.id = v.comprobante_id
        WHERE dv.producto_id = p_producto_id
          AND v.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
    ) AS movimientos
    ORDER BY fecha;


    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- 1. Obtener stock_inicial y fecha_registro
    SELECT stock_inicial, fecha_registro INTO v_saldo, v_fecha_registro
    FROM productos
    WHERE id = p_producto_id;

    -- 2. Agregar entradas previas al rango
    SELECT IFNULL(SUM(dc.cantidad), 0)
    INTO @entradas_antes
    FROM compras c
    JOIN detalles_compra dc ON dc.compra_id = c.id
    WHERE dc.producto_id = p_producto_id AND c.fecha < p_fecha_inicio;

    -- 3. Agregar salidas previas al rango
    SELECT IFNULL(SUM(dv.cantidad), 0)
    INTO @salidas_antes
    FROM ventas v
    JOIN detalles_venta dv ON dv.venta_id = v.id
    WHERE dv.producto_id = p_producto_id AND v.fecha < p_fecha_inicio;

    -- 4. Calcular saldo inicial acumulado
    SET v_saldo = v_saldo + @entradas_antes - @salidas_antes;

    -- 5. Crear tabla temporal
    DROP TEMPORARY TABLE IF EXISTS tmp_kardex;
    CREATE TEMPORARY TABLE tmp_kardex (
        fecha DATETIME,
        tipo VARCHAR(20),
        detalle VARCHAR(200),
        cantidad INT,
        saldo INT
    );

    -- 6. Insertar saldo inicial con fecha_registro
    INSERT INTO tmp_kardex (fecha, tipo, detalle, cantidad, saldo)
	 VALUES (DATE(v_fecha_registro), 'SALDO INICIAL', 'Saldo acumulado antes del rango', 0, v_saldo);


    -- 7. Ejecutar cursor
    OPEN cur;

    bucle_kardex: LOOP
        FETCH cur INTO v_fecha, v_tipo, v_detalle, v_cantidad;
        IF done THEN
            LEAVE bucle_kardex;
        END IF;

        SET v_saldo = v_saldo + v_cantidad;

        INSERT INTO tmp_kardex (fecha, tipo, detalle, cantidad, saldo)
        VALUES (v_fecha, v_tipo, v_detalle, v_cantidad, v_saldo);
    END LOOP;

    CLOSE cur;

    -- 8. Mostrar Kardex final
    SELECT * FROM tmp_kardex ORDER BY fecha;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS resumen_ventas_por_rango;

DELIMITER //

CREATE PROCEDURE resumen_ventas_por_rango (
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    SELECT
        venta_id,
        fecha,
        num_comprobante,
        cliente,
        tipo_comprobante,
        estado,
        subtotal,
        valor_impuesto,
        valor_descuento,
        subtotal + valor_impuesto - valor_descuento AS total
    FROM (
        SELECT
            v.id AS venta_id,
            DATE(v.fecha) AS fecha,
            v.num_comprobante,
            c.nombre AS cliente,
            comp.nombre AS tipo_comprobante,
            e.nombre AS estado,
            ROUND(SUM(dv.cantidad * dv.precio), 2) AS subtotal,
            ROUND((v.impuesto / 100) * SUM(dv.cantidad * dv.precio), 2) AS valor_impuesto,
            ROUND(
                (v.descuento / 100) *
                (
                    SUM(dv.cantidad * dv.precio) +
                    (v.impuesto / 100) * SUM(dv.cantidad * dv.precio)
                ), 2
            ) AS valor_descuento
        FROM ventas v
        JOIN detalles_venta dv ON dv.venta_id = v.id
        JOIN clientes c ON c.id = v.cliente_id
        JOIN comprobantes comp ON comp.id = v.comprobante_id
        JOIN estados e ON e.id = v.estado_id
        WHERE v.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
        GROUP BY v.id, v.fecha, v.num_comprobante, c.nombre, comp.nombre, e.nombre, v.impuesto, v.descuento
    ) AS sub
    ORDER BY fecha, venta_id;
END //

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE resumen_compras_por_rango(
    IN fecha_inicio DATE,
    IN fecha_fin DATE
)
BEGIN
    SELECT
        c.id AS compra_id,
        c.fecha,
        c.num_comprobante,
        p.nombre AS proveedor,
        cp.nombre AS tipo_comprobante,
        e.nombre AS estado,
        SUM(dc.cantidad * dc.costo) AS subtotal
    FROM compras c
    INNER JOIN proveedores p ON c.proveedor_id = p.id
    INNER JOIN comprobantes cp ON c.comprobante_id = cp.id
    INNER JOIN estados e ON c.estado_id = e.id
    INNER JOIN detalles_compra dc ON c.id = dc.compra_id
    WHERE DATE(c.fecha) BETWEEN fecha_inicio AND fecha_fin
    GROUP BY c.id, c.fecha, c.num_comprobante, p.nombre, cp.nombre, e.nombre
    ORDER BY c.fecha ASC;
END$$

DELIMITER ;

CALL kardex_con_saldo(2, '2025-01-01 00:00:00', '2025-12-31 23:59:59');

-- ================================================
-- INSERTS INICIALES
-- ================================================

INSERT INTO roles(nombre) VALUES ('Desarrollador'),('Administramodulosdor'), ('Operador');

INSERT INTO usuarios(username, password, nombres, apellidos, cargo, rol_id, fecha_registro, fecha_actualizado, activo) VALUES
('darknet', 'davian', 'Roy', 'Paredes', 'Desarrollador', 1, NOW(), NOW(), 1),
('david', 'david123', 'David', 'Huayrana', 'Administrador', 2, NOW(), NOW(), 1),
('roger', '12345', 'Roger', 'Bellido', 'Operador', 3, NOW(), NOW(), 1);

INSERT INTO modulos(nombre, activo) VALUES
('Inicio', 1),
('Productos', 1),
('Entradas', 1),
('Salidas', 1),
('Gastos', 1),
('Reportes', 1),
('Setup', 1),
('Logout',1);

INSERT INTO rol_modulo (rol_id, modulo_id) VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),
(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(2,7),
(3,1),(3,2),(3,3),(3,4);

INSERT INTO comprobantes(nombre) VALUES
('FACTURA'),('RECIBO'),('BOLETA'),('NOTA DE CRÉDITO'),('NOTA DE DÉBITO');

INSERT INTO estados(nombre) VALUES
('PENDIENTE'),('PAGADO'),('ANULADO'),('EN PROCESO'),('COMPLETADO');

INSERT INTO transacciones(nombre) VALUES
('COMPRA'),('VENTA'),('DEVOLUCIÓN'),('AJUSTE DE STOCK'),('TRASPASO'),('OTRO');



INSERT INTO categorias(nombre) VALUES ('MATERIA PRIMA'), ('HERRAMIENTAS');

INSERT INTO categorias_gastos(nombre, activo) VALUES
('Alquiler', 1),
('Servicios Básicos', 1),
('Salarios', 1),
('Transporte', 1),
('Otros', 1);

INSERT INTO productos(codigo, categoria_id, descripcion, marca, procedencia, peso, stock_inicial, stock_actual, stock_minimo, usuario_id) VALUES
('P001', 1, 'Tornillo de acero', 'ACME', 'Brasil', '0.5kg', 100, 100, 10, 1),
('P002', 2, 'Martillo profesional', 'STANLEY', 'China', '1kg', 50, 50, 5, 2);

INSERT INTO proveedores(nombre, nit, materiales, contacto, celular_contacto, email_contacto) VALUES
('Industrias BOLT', '123456789', 'Tornillos, Tuercas', 'Carlos Rivera', '78945612', 'carlos@bolt.com'),
('Ferretería Central', '987654321', 'Herramientas', 'Lucía Prado', '71234567', 'lucia@central.com');

INSERT INTO clientes(nombre, nit, celular, direccion) VALUES
('Juan Pérez', '56789012', '71234567', 'Av. Siempre Viva 123'),
('María García', '23456789', '78912345', 'Calle Falsa 456');


ALTER USER 'rhino'@'%' IDENTIFIED BY 'gyrx100PRE#';

ALTER TABLE productos
CHANGE COLUMN procedencia precio DECIMAL(10,2) NOT null;

ALTER TABLE productos
MODIFY COLUMN peso DECIMAL(10,2) NOT null;

UPDATE productos
SET procedencia = '0.0',
    peso = '0.0';

DESC productos;

ALTER TABLE productos
ADD CONSTRAINT codigo UNIQUE (codigo);

ALTER TABLE comprobantes
ADD COLUMN numero INT DEFAULT 1 NOT NULL;

SELECT * FROM comprobantes;




