
ALTER USER 'rhino'@'%' IDENTIFIED BY 'gyrx100PRE#';

ALTER TABLE productos
CHANGE COLUMN procedencia precio DECIMAL(10,2) NOT null;

ALTER TABLE productos
MODIFY COLUMN peso DECIMAL(10,2) NOT null;

UPDATE productos
SET procedencia = '0.0',
    peso = '0.0';

ALTER TABLE productos
ADD CONSTRAINT codigo UNIQUE (codigo);

ALTER TABLE comprobantes
MODIFY COLUMN numero INT DEFAULT 1 NOT NULL;

ALTER TABLE comprobantes
ADD COLUMN numero INT DEFAULT 1 NOT NULL;

ALTER TABLE productos
ADD COLUMN utilidad DECIMAL(10,2) DEFAULT 0 NOT NULL AFTER peso;

ALTER TABLE detalles_venta
ADD COLUMN utilidad DECIMAL(10,2) DEFAULT 0 NOT NULL;

ALTER TABLE ventas
ADD COLUMN correlativo TINYINT(1) DEFAULT 0 AFTER num_comprobante;


----------------------------------- implementar

ALTER TABLE compras
ADD COLUMN activo TINYINT(1) DEFAULT 0;

UPDATE compras SET activo = 1 WHERE estado_id = 3;
UPDATE compras SET estado_id=1 where estado_id = 3;

ALTER TABLE ventas
ADD COLUMN activo TINYINT(1) DEFAULT 0;

UPDATE ventas SET activo = 1 WHERE estado_id = 3;
UPDATE ventas SET estado_id=1 where estado_id = 3;

ALTER TABLE categorias
MODIFY COLUMN nombre VARCHAR(100) NOT NULL UNIQUE;

