"""unidades de medida: tablas categorias_unidad, unidades_medida, producto_unidades; alter detalles_cotizacion; seed modulos

Revision ID: a1b2c3d4e5f6
Revises: f3c7a91b2d84
Create Date: 2026-08-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f3c7a91b2d84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Tablas nuevas ──
    op.create_table(
        'categorias_unidad',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('1'), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    op.create_table(
        'unidades_medida',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('abreviatura', sa.String(length=20), nullable=True),
        sa.Column('categoria_unidad_id', sa.Integer(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.text('1'), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        sa.ForeignKeyConstraint(['categoria_unidad_id'], ['categorias_unidad.id']),
    )

    op.create_table(
        'producto_unidades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('unidad_id', sa.Integer(), nullable=False),
        sa.Column('es_principal', sa.Boolean(), server_default=sa.text('0'), nullable=True),
        sa.Column('factor_conversion', sa.Numeric(18, 4), server_default='1', nullable=False),
        sa.Column('fecha_registro', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizado', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
        sa.ForeignKeyConstraint(['unidad_id'], ['unidades_medida.id']),
        sa.UniqueConstraint('producto_id', 'unidad_id', name='uq_producto_unidad'),
    )

    # ── Alter detalles_cotizacion ──
    op.add_column('detalles_cotizacion', sa.Column('unidad_id', sa.Integer(), nullable=True))
    op.alter_column('detalles_cotizacion', 'cantidad', type_=sa.Numeric(10, 2), existing_nullable=False)
    op.drop_column('detalles_cotizacion', 'dias_disponibilidad')

    # ── Seed: Categorías de unidad ──
    categorias = [
        ('PESO', 'Unidades de masa'),
        ('VOLUMEN', 'Unidades de volumen líquido'),
        ('LONGITUD', 'Unidades de longitud lineal'),
        ('SUPERFICIE', 'Unidades de área'),
        ('VOLUMEN CÚBICO', 'Unidades de volumen cúbico'),
        ('CANTIDAD', 'Unidades de conteo/empaque'),
        ('EMPAQUE/ENVASE', 'Envases y empaques'),
        ('FARMACÉUTICO', 'Unidades farmacéuticas'),
        ('ENERGÍA', 'Unidades de energía/potencia'),
        ('GAS NATURAL', 'Unidades de gas y volumen industrial'),
        ('TIEMPO', 'Unidades de tiempo'),
        ('OTROS', 'Otras unidades'),
    ]
    for nombre, desc in categorias:
        op.execute(
            f"INSERT IGNORE INTO categorias_unidad (nombre, descripcion, activo, fecha_registro, fecha_actualizado) "
            f"VALUES ('{nombre}', '{desc}', 1, NOW(), NOW())"
        )

    # ── Seed: Unidades de medida ──
    unidades = [
        # PESO
        ('GRAMO', 'g', 'PESO'), ('KILOGRAMO', 'kg', 'PESO'), ('MILIGRAMOS', 'mg', 'PESO'),
        ('LIBRAS', 'lb', 'PESO'), ('ONZAS', 'oz', 'PESO'), ('QUINTAL', 'qq', 'PESO'),
        ('ARROBA', 'arroba', 'PESO'), ('TONELADAS', 'ton', 'PESO'),
        ('TONELADA CORTA', 'ton corta', 'PESO'), ('TONELADA LARGA', 'ton larga', 'PESO'),
        ('TONELADA METRICA', 'ton metrica', 'PESO'),
        # VOLUMEN
        ('LITRO', 'L', 'VOLUMEN'), ('MILILITRO', 'mL', 'VOLUMEN'), ('HECTOLITRO', 'hL', 'VOLUMEN'),
        ('GALON INGLES', 'gal ing', 'VOLUMEN'), ('US GALON (3,7843 L)', 'US gal', 'VOLUMEN'),
        ('BIDÓN', 'bidon', 'VOLUMEN'), ('TAMBOR', 'tambor', 'VOLUMEN'), ('BARRILES', 'barril', 'VOLUMEN'),
        ('BARRIL [42 GALONES(EEUU)]', 'bbl 42', 'VOLUMEN'), ('BARRIL (EEUU) 60 F', 'bbl 60F', 'VOLUMEN'),
        ('POTE', 'pote', 'VOLUMEN'), ('POMO', 'pomo', 'VOLUMEN'), ('VASO', 'vaso', 'VOLUMEN'),
        # LONGITUD
        ('METRO', 'm', 'LONGITUD'), ('KILOMETRO', 'km', 'LONGITUD'),
        ('CENTIMETRO LINEAL', 'cm', 'LONGITUD'), ('MILIMETRO', 'mm', 'LONGITUD'),
        ('PULGADAS', 'pulg', 'LONGITUD'), ('PIES', 'ft', 'LONGITUD'), ('YARDA', 'yd', 'LONGITUD'),
        # SUPERFICIE
        ('METRO CUADRADO', 'm²', 'SUPERFICIE'), ('CENTIMETRO CUADRADO', 'cm²', 'SUPERFICIE'),
        ('MILIMETRO CUADRADO', 'mm²', 'SUPERFICIE'), ('PIES CUADRADOS', 'ft²', 'SUPERFICIE'),
        ('YARDA CUADRADA', 'yd²', 'SUPERFICIE'), ('HECTAREAS', 'ha', 'SUPERFICIE'),
        ('PLIEGO', 'pliego', 'SUPERFICIE'),
        # VOLUMEN CÚBICO
        ('METRO CUBICO', 'm³', 'VOLUMEN CÚBICO'), ('CENTIMETRO CUBICO', 'cm³', 'VOLUMEN CÚBICO'),
        ('MILIMETRO CUBICO', 'mm³', 'VOLUMEN CÚBICO'), ('PIES CUBICOS', 'ft³', 'VOLUMEN CÚBICO'),
        # CANTIDAD
        ('UNIDAD (BIENES)', 'u.b.', 'CANTIDAD'), ('UNIDAD (SERVICIOS)', 'u.s.', 'CANTIDAD'),
        ('CIENTO DE UNIDADES', 'ciento', 'CANTIDAD'), ('DOCENA', 'doc', 'CANTIDAD'),
        ('MILLARES', 'millar', 'CANTIDAD'), ('MILLON DE UNIDADES', 'millon', 'CANTIDAD'),
        ('PAR', 'par', 'CANTIDAD'), ('JUEGO', 'juego', 'CANTIDAD'), ('CONJUNTO', 'conj', 'CANTIDAD'),
        ('KIT', 'kit', 'CANTIDAD'), ('PIEZAS', 'pza', 'CANTIDAD'), ('PACK', 'pack', 'CANTIDAD'),
        ('PAQUETE', 'paq', 'CANTIDAD'), ('BARRA', 'barra', 'CANTIDAD'), ('TIRA', 'tira', 'CANTIDAD'),
        ('PLACAS', 'placa', 'CANTIDAD'), ('HOJA', 'hoja', 'CANTIDAD'), ('CONOS', 'cono', 'CANTIDAD'),
        ('CILINDRO', 'cil', 'CANTIDAD'), ('TUBOS', 'tubo', 'CANTIDAD'), ('TUBO', 'tubo', 'CANTIDAD'),
        ('PIE TABLAR', 'pie tablar', 'CANTIDAD'),
        # EMPAQUE/ENVASE
        ('BOLSA', 'bolsa', 'EMPAQUE/ENVASE'), ('CAJA', 'caja', 'EMPAQUE/ENVASE'),
        ('CARTONES', 'carton', 'EMPAQUE/ENVASE'), ('BOBINAS', 'bobina', 'EMPAQUE/ENVASE'),
        ('ROLLO', 'rollo', 'EMPAQUE/ENVASE'), ('RESMA', 'resma', 'EMPAQUE/ENVASE'),
        ('FARDO', 'fardo', 'EMPAQUE/ENVASE'), ('BULTO', 'bulto', 'EMPAQUE/ENVASE'),
        ('BANDEJA', 'bandeja', 'EMPAQUE/ENVASE'), ('JABA', 'jaba', 'EMPAQUE/ENVASE'),
        ('CARTOLA', 'cartola', 'EMPAQUE/ENVASE'), ('TETRAPACK', 'tetra', 'EMPAQUE/ENVASE'),
        ('MINI BOTELLA', 'mini bot', 'EMPAQUE/ENVASE'), ('BOTELLAS', 'botella', 'EMPAQUE/ENVASE'),
        ('SACHET', 'sachet', 'EMPAQUE/ENVASE'), ('SOBRES', 'sobre', 'EMPAQUE/ENVASE'),
        ('ESTUCHE', 'estuche', 'EMPAQUE/ENVASE'), ('BLISTER', 'blister', 'EMPAQUE/ENVASE'),
        ('TURRIL', 'turril', 'EMPAQUE/ENVASE'), ('FRASCO', 'frasco', 'EMPAQUE/ENVASE'),
        ('LATAS', 'lata', 'EMPAQUE/ENVASE'), ('TERMO', 'termo', 'EMPAQUE/ENVASE'),
        ('BALDE', 'balde', 'EMPAQUE/ENVASE'), ('PALETAS', 'paleta', 'EMPAQUE/ENVASE'),
        ('AEROSOL', 'aerosol', 'EMPAQUE/ENVASE'),
        # FARMACÉUTICO
        ('AMPOLLA', 'ampolla', 'FARMACÉUTICO'), ('CAPSULA', 'capsula', 'FARMACÉUTICO'),
        ('COMPRIMIDO', 'comp', 'FARMACÉUTICO'), ('TABLETA', 'tab', 'FARMACÉUTICO'),
        ('PASTILLA', 'past', 'FARMACÉUTICO'), ('OVULOS', 'ovulo', 'FARMACÉUTICO'),
        ('SUPOSITORIOS', 'supos', 'FARMACÉUTICO'), ('JERINGA', 'jeringa', 'FARMACÉUTICO'),
        ('VIAL', 'vial', 'FARMACÉUTICO'), ('PIPETA', 'pipeta', 'FARMACÉUTICO'),
        ('FANEGA', 'fanega', 'FARMACÉUTICO'),
        # ENERGÍA
        ('KILOWATT', 'kW', 'ENERGÍA'), ('MEGAWATT', 'MW', 'ENERGÍA'),
        ('KILOVATIO HORA', 'kWh', 'ENERGÍA'), ('MEGAWATT HORA', 'MWh', 'ENERGÍA'),
        ('UNIDAD TERMICA BRITANICA (TI)', 'BTU', 'ENERGÍA'),
        ('MILLONES DE BTU (1000000 BTU)', 'MMBTU', 'ENERGÍA'),
        # GAS NATURAL
        ('MILLONES DE PIES CUBICOS (1000000 PC)', 'MMPC', 'GAS NATURAL'),
        ('MILLAR DE PIES CUBICOS (1000 PC)', 'MPC', 'GAS NATURAL'),
        ('MIL PIES CUBICOS 14696 PSI 68FAH', 'MPC 68F', 'GAS NATURAL'),
        ('MIL PIES CUBICOS 14696 PSI', 'MPC 14.7', 'GAS NATURAL'),
        ('METRO CUBICO 68F VOL', 'm³ 68F', 'GAS NATURAL'),
        # TIEMPO
        ('HORAS', 'h', 'TIEMPO'), ('MESES', 'mes', 'TIEMPO'),
        ('AMORTIZACION', 'amort', 'TIEMPO'),
        # OTROS
        ('OTRO', 'otro', 'OTROS'), ('EQUIPOS', 'equipo', 'OTROS'),
    ]
    for nombre, abrev, cat in unidades:
        op.execute(
            f"INSERT IGNORE INTO unidades_medida (nombre, abreviatura, categoria_unidad_id, activo, fecha_registro, fecha_actualizado) "
            f"SELECT '{nombre}', '{abrev}', id, 1, NOW(), NOW() FROM categorias_unidad WHERE nombre = '{cat}'"
        )

    # ── Seed: Módulos para permisos ──
    op.execute("INSERT IGNORE INTO modulos (nombre, activo) VALUES ('Unidades de Medida', 1)")
    op.execute("INSERT IGNORE INTO modulos (nombre, activo) VALUES ('Categorías de Unidad', 1)")
    op.execute("INSERT IGNORE INTO rol_modulo (rol_id, modulo_id) SELECT 1, id FROM modulos WHERE nombre = 'Unidades de Medida'")
    op.execute("INSERT IGNORE INTO rol_modulo (rol_id, modulo_id) SELECT 1, id FROM modulos WHERE nombre = 'Categorías de Unidad'")


def downgrade() -> None:
    op.execute("DELETE FROM rol_modulo WHERE modulo_id IN (SELECT id FROM modulos WHERE nombre IN ('Unidades de Medida', 'Categorías de Unidad'))")
    op.execute("DELETE FROM modulos WHERE nombre IN ('Unidades de Medida', 'Categorías de Unidad')")
    op.execute("DELETE FROM producto_unidades")
    op.execute("DELETE FROM unidades_medida")
    op.execute("DELETE FROM categorias_unidad")
    op.drop_table('producto_unidades')
    op.drop_table('unidades_medida')
    op.drop_table('categorias_unidad')
    op.add_column('detalles_cotizacion', sa.Column('dias_disponibilidad', sa.Integer(), nullable=True))
    op.alter_column('detalles_cotizacion', 'cantidad', type_=sa.Integer(), existing_nullable=False)
    op.drop_column('detalles_cotizacion', 'unidad_id')
