
CREATE TABLE productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(50) NOT NULL,
  categoria_id INT,
  descripcion TEXT NOT NULL,
  marca VARCHAR(50) NOT NULL,
  precio DECIMAL(10,2) DEFAULT 0 NOT null,
  utilidad DECIMAL(10,2) DEFAULT 0 NOT NULL,
  peso DECIMAL(10,2) DEFAULT 0 NOT null,
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

CREATE TABLE clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  nit VARCHAR(20) NOT NULL,
  celular VARCHAR(20) NOT NULL,
  direccion TEXT NOT NULL,
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

CREATE TABLE ventas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME NOT NULL,
  cliente_id INT,
  comprobante_id INT,
  correlativo TINYINT(1) DEFAULT 0,
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
  utilidad DECIMAL(10,2) DEFAULT 0 NOT NULL,
  FOREIGN KEY (venta_id) REFERENCES ventas(id),
  FOREIGN KEY (producto_id) REFERENCES productos(id)
);
