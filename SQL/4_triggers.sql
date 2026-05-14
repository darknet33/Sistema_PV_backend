DELIMITER $$

-- DETALLE VENTA
DROP TRIGGER IF EXISTS tr_insertar_detalle_venta $$
CREATE TRIGGER tr_insertar_detalle_venta AFTER INSERT ON detalles_venta FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual - NEW.cantidad WHERE id = NEW.producto_id;
  -- UPDATE ventas SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = NEW.venta_id) WHERE id = NEW.venta_id;
END $$

DROP TRIGGER IF EXISTS tr_actualizar_detalle_venta $$
CREATE TRIGGER tr_actualizar_detalle_venta AFTER UPDATE ON detalles_venta FOR EACH ROW
BEGIN
  IF OLD.producto_id = NEW.producto_id THEN
    UPDATE productos SET stock_actual = stock_actual + OLD.cantidad - NEW.cantidad WHERE id = NEW.producto_id;
  ELSE
    UPDATE productos SET stock_actual = stock_actual + OLD.cantidad WHERE id = OLD.producto_id;
    UPDATE productos SET stock_actual = stock_actual - NEW.cantidad WHERE id = NEW.producto_id;
  END IF;
  -- UPDATE ventas as v SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = NEW.venta_id) WHERE id = NEW.venta_id;
END $$

DROP TRIGGER IF EXISTS tr_borrar_detalle_venta $$
CREATE TRIGGER tr_borrar_detalle_venta AFTER DELETE ON detalles_venta FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual + OLD.cantidad WHERE id = OLD.producto_id;
  -- UPDATE ventas SET total = (SELECT IFNULL(SUM(cantidad * precio), 0) FROM detalles_venta WHERE venta_id = OLD.venta_id) WHERE id = OLD.venta_id;
END $$

-- DETALLE COMPRA
DROP TRIGGER IF EXISTS tr_insertar_detalle_compra $$
CREATE TRIGGER tr_insertar_detalle_compra AFTER INSERT ON detalles_compra FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual + NEW.cantidad WHERE id = NEW.producto_id;
  UPDATE compras SET total = (SELECT IFNULL(SUM(cantidad * costo), 0) FROM detalles_compra WHERE compra_id = NEW.compra_id) WHERE id = NEW.compra_id;
END $$

DROP TRIGGER IF EXISTS tr_actualizar_detalle_compra $$
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

DROP TRIGGER IF EXISTS tr_borrar_detalle_compra $$
CREATE TRIGGER tr_borrar_detalle_compra AFTER DELETE ON detalles_compra FOR EACH ROW
BEGIN
  UPDATE productos SET stock_actual = stock_actual - OLD.cantidad WHERE id = OLD.producto_id;
  UPDATE compras SET total = (SELECT IFNULL(SUM(cantidad * costo), 0) FROM detalles_compra WHERE compra_id = OLD.compra_id) WHERE id = OLD.compra_id;
END $$

-- PRECIO Y UTILIDAD
DROP TRIGGER IF EXISTS tr_insertar_precio_after_compra $$
CREATE TRIGGER tr_insertar_precio_after_compra AFTER INSERT ON detalles_compra FOR EACH ROW
BEGIN
  DECLARE nuevo_precio DECIMAL(10,2);
  SET nuevo_precio = NEW.costo;
  UPDATE productos SET precio = nuevo_precio WHERE id = NEW.producto_id AND nuevo_precio > precio;
END $$

DROP TRIGGER IF EXISTS tr_actualizar_precio_after_compra $$
CREATE TRIGGER tr_actualizar_precio_after_compra AFTER UPDATE ON detalles_compra FOR EACH ROW
BEGIN
  DECLARE nuevo_precio DECIMAL(10,2);
  SET nuevo_precio = NEW.costo;
  UPDATE productos SET precio = nuevo_precio WHERE id = NEW.producto_id AND nuevo_precio > precio;
END $$

DROP TRIGGER IF EXISTS tr_insertar_utilidad_after_venta $$
CREATE TRIGGER tr_insertar_utilidad_after_venta AFTER INSERT ON detalles_venta FOR EACH ROW
BEGIN
  DECLARE nueva_utilidad DECIMAL(10,2);
  SET nueva_utilidad = NEW.utilidad;
  UPDATE productos SET utilidad = nueva_utilidad WHERE id = NEW.producto_id AND nueva_utilidad > utilidad;
END $$

DROP TRIGGER IF EXISTS tr_actualizar_utilidad_after_venta $$
CREATE TRIGGER tr_actualizar_utilidad_after_venta AFTER UPDATE ON detalles_venta FOR EACH ROW
BEGIN
  DECLARE nueva_utilidad DECIMAL(10,2);
  SET nueva_utilidad = NEW.utilidad;
  UPDATE productos SET utilidad = nueva_utilidad WHERE id = NEW.producto_id AND nueva_utilidad > utilidad;
END $$

DELIMITER ;
