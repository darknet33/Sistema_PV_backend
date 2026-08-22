"""gastos tablas de gasto y categoria de gasto

Revision ID: f3c7a91b2d84
Revises: b1c2d3e4f5a6
Create Date: 2026-08-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3c7a91b2d84'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('categorias_gastos',
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.Column('fecha_actualizado', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('gastos',
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.Column('categoria_gasto_id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('monto', sa.DECIMAL(10, 2), nullable=False),
    sa.Column('estado_id', sa.Integer(), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.Column('fecha_actualizado', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['categoria_gasto_id'], ['categorias_gastos.id'], ),
    sa.ForeignKeyConstraint(['estado_id'], ['estados.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute("INSERT INTO categorias_gastos(nombre, activo) VALUES ('Alquiler', 1), ('Servicios Básicos', 1), ('Salarios', 1), ('Transporte', 1), ('Otros', 1)")
    op.execute("INSERT IGNORE INTO modulos(nombre, activo) VALUES ('Gastos', 1)")
    op.execute("INSERT IGNORE INTO rol_modulo (rol_id, modulo_id) SELECT 1, id FROM modulos WHERE nombre = 'Gastos'")
    op.execute("INSERT IGNORE INTO modulos(nombre, activo) VALUES ('Modulos', 1)")
    op.execute("INSERT IGNORE INTO rol_modulo (rol_id, modulo_id) SELECT 1, id FROM modulos WHERE nombre = 'Modulos'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('gastos')
    op.drop_table('categorias_gastos')
