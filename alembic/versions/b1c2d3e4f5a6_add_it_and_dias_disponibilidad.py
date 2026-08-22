"""add it to cotizaciones/ventas and dias_disponibilidad to cotizacion_detalle

Revision ID: b1c2d3e4f5a6
Revises: df08dc1086a7
Create Date: 2026-08-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a27353ed7982'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cotizaciones', sa.Column('it', sa.DECIMAL(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('ventas', sa.Column('it', sa.DECIMAL(precision=10, scale=2), nullable=True, server_default='0'))
    op.add_column('detalles_cotizacion', sa.Column('dias_disponibilidad', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('detalles_cotizacion', 'dias_disponibilidad')
    op.drop_column('ventas', 'it')
    op.drop_column('cotizaciones', 'it')
