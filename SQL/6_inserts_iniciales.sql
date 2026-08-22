
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

INSERT INTO productos(codigo, categoria_id, descripcion, marca, precio, peso, stock_inicial, stock_actual, stock_minimo, usuario_id) VALUES
('P001', 1, 'Tornillo de acero', 'ACME', 2.00, 0.5, 100, 100, 10, 1),
('P002', 2, 'Martillo profesional', 'STANLEY', 8.00, 1.0, 50, 50, 5, 2);

INSERT INTO proveedores(nombre, nit, materiales, contacto, celular_contacto, email_contacto) VALUES
('Industrias BOLT', '123456789', 'Tornillos, Tuercas', 'Carlos Rivera', '78945612', 'carlos@bolt.com'),
('Ferretería Central', '987654321', 'Herramientas', 'Lucía Prado', '71234567', 'lucia@central.com');

INSERT INTO clientes(nombre, nit, celular, direccion) VALUES
('Juan Pérez', '56789012', '71234567', 'Av. Siempre Viva 123'),
('María García', '23456789', '78912345', 'Calle Falsa 456');
