"""backfill timestamps nulos en gastos y categorias_gastos

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE categorias_gastos SET fecha_registro = NOW(), fecha_actualizado = NOW() WHERE fecha_registro IS NULL")
    op.execute("UPDATE categorias_gastos SET fecha_actualizado = NOW() WHERE fecha_actualizado IS NULL")
    op.execute("UPDATE gastos SET fecha_registro = NOW(), fecha_actualizado = NOW() WHERE fecha_registro IS NULL")
    op.execute("UPDATE gastos SET fecha_actualizado = NOW() WHERE fecha_actualizado IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    pass