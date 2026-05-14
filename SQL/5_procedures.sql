DELIMITER $$

-- =======================================
-- PROCEDIMIENTO: kardex_con_saldo
-- =======================================
DROP PROCEDURE IF EXISTS kardex_con_saldo $$

CREATE PROCEDURE kardex_con_saldo (
    IN p_producto_id INT,
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_fecha DATETIME;
    DECLARE v_tipo VARCHAR(20);
    DECLARE v_detalle VARCHAR(200);
    DECLARE v_cantidad INT;
    DECLARE v_saldo INT;
    DECLARE v_fecha_registro DATETIME;

    DECLARE cur CURSOR FOR 
        SELECT DATE(fecha) AS fecha, tipo, detalle, cantidad
        FROM (
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

    SELECT stock_inicial, fecha_registro INTO v_saldo, v_fecha_registro
    FROM productos
    WHERE id = p_producto_id;

    SELECT IFNULL(SUM(dc.cantidad), 0)
    INTO @entradas_antes
    FROM compras c
    JOIN detalles_compra dc ON dc.compra_id = c.id
    WHERE dc.producto_id = p_producto_id AND c.fecha < p_fecha_inicio;

    SELECT IFNULL(SUM(dv.cantidad), 0)
    INTO @salidas_antes
    FROM ventas v
    JOIN detalles_venta dv ON dv.venta_id = v.id
    WHERE dv.producto_id = p_producto_id AND v.fecha < p_fecha_inicio;

    SET v_saldo = v_saldo + @entradas_antes - @salidas_antes;

    DROP TEMPORARY TABLE IF EXISTS tmp_kardex;
    CREATE TEMPORARY TABLE tmp_kardex (
        fecha DATETIME,
        tipo VARCHAR(20),
        detalle VARCHAR(200),
        cantidad INT,
        saldo INT
    );

    INSERT INTO tmp_kardex (fecha, tipo, detalle, cantidad, saldo)
    VALUES (DATE(v_fecha_registro), 'SALDO INICIAL', 'Saldo acumulado antes del rango', 0, v_saldo);

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

    SELECT * FROM tmp_kardex ORDER BY fecha;
END $$


-- =======================================
-- PROCEDIMIENTO: resumen_ventas_por_rango
-- =======================================
DROP PROCEDURE IF EXISTS resumen_ventas_por_rango $$

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
        subtotal + valor_impuesto - valor_descuento AS total,
        utilidad_bruta
    FROM (
        SELECT
            v.id AS venta_id,
            DATE(v.fecha) AS fecha,
            v.num_comprobante,
            c.nombre AS cliente,
            comp.nombre AS tipo_comprobante,
            e.nombre AS estado,
            ROUND(SUM(dv.cantidad * dv.precio), 2) AS subtotal,
            ROUND((SUM(dv.cantidad * dv.precio)*(v.impuesto / 100)/(1-(v.impuesto / 100))) , 2) AS valor_impuesto,
            ROUND(SUM(dv.cantidad * dv.precio)*(v.descuento/100)/(1-(v.impuesto / 100)), 2) AS valor_descuento,
            ROUND(SUM(dv.cantidad * dv.utilidad),2) AS utilidad_bruta
        FROM ventas v
        JOIN detalles_venta dv ON dv.venta_id = v.id
        JOIN clientes c ON c.id = v.cliente_id
        JOIN comprobantes comp ON comp.id = v.comprobante_id
        JOIN estados e ON e.id = v.estado_id
        WHERE v.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
        GROUP BY v.id, v.fecha, v.num_comprobante, c.nombre, comp.nombre, e.nombre, v.impuesto, v.descuento
    ) AS sub
    ORDER BY fecha, venta_id;
END $$


-- =======================================
-- PROCEDIMIENTO: resumen_compras_por_rango
-- =======================================
DROP PROCEDURE IF EXISTS resumen_compras_por_rango $$

CREATE PROCEDURE resumen_compras_por_rango (
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
END $$


-- =======================================
-- PROCEDIMIENTO: sp_productos_mas_vendidos
-- =======================================
DROP PROCEDURE IF EXISTS sp_productos_mas_vendidos $$

CREATE PROCEDURE sp_productos_mas_vendidos (
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME,
    IN p_limite INT
)
BEGIN
    SELECT 
        p.id,
        CONCAT(
            p.codigo, ' ',
            IFNULL(c.nombre, 'SinCategoria'), ' ',
            p.descripcion, ' ',
            p.marca
        ) AS descripcion_completa,
        SUM(dv.cantidad) AS total_vendido
    FROM detalles_venta dv
    INNER JOIN ventas v ON v.id = dv.venta_id
    INNER JOIN productos p ON p.id = dv.producto_id
    LEFT JOIN categorias c ON c.id = p.categoria_id
    WHERE v.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
    GROUP BY p.id, descripcion_completa
    ORDER BY total_vendido DESC
    LIMIT p_limite;
END$$

-- =======================================
-- PROCEDIMIENTO: sp_total_ventas_rango
-- =======================================
DROP PROCEDURE IF EXISTS sp_total_ventas_rango $$
CREATE PROCEDURE sp_total_ventas_rango (
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    -- Totales directos de ventas
    SELECT 
        COUNT(*) AS cantidad_ventas,
        SUM(total) AS total_ventas
    INTO @cantidad_ventas, @total_ventas
    FROM ventas
    WHERE fecha BETWEEN p_fecha_inicio AND p_fecha_fin  AND total > 0;

    -- Totales detallados
    SELECT
        @cantidad_ventas AS cantidad_ventas,
        @total_ventas AS total_ventas,

        -- Total impuesto corregido
        SUM(
            CASE 
                WHEN v.impuesto > 0 THEN 
                    dv.precio * (v.impuesto / (100 - v.impuesto)) * dv.cantidad
                ELSE 0
            END
        ) AS total_impuestos,

        -- Total descuento corregido para ser consistente con resumen
        SUM(
            CASE
                WHEN v.descuento > 0 THEN
                    (dv.precio / (1 - v.impuesto / 100)) * (v.descuento / 100) * dv.cantidad
                ELSE 0
            END
        ) AS total_descuentos,

        -- Utilidad total
        SUM(dv.utilidad * dv.cantidad) AS total_utilidad

    FROM ventas v
    JOIN detalles_venta dv ON dv.venta_id = v.id
    WHERE v.fecha BETWEEN p_fecha_inicio AND p_fecha_fin;
END $$

-- =======================================
-- PROCEDIMIENTO: sp_total_compras_rango
-- =======================================
DROP PROCEDURE IF EXISTS sp_total_compras_rango $$

CREATE PROCEDURE sp_total_compras_rango (
    IN p_fecha_inicio DATETIME,
    IN p_fecha_fin DATETIME
)
BEGIN
    SELECT 
        COUNT(c.id) AS cantidad_compras,
        SUM(c.total) AS total_compras
    FROM compras c
    WHERE c.fecha BETWEEN p_fecha_inicio AND p_fecha_fin and c.total > 0;
END $$

DELIMITER ;
