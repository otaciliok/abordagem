"""Adicionar coluna alerta manualmente

Revision ID: fb58eb39f2f5
Revises: 
Create Date: 2025-04-05 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb58eb39f2f5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona a coluna alerta com valor padrão False
    op.add_column('abordagem', sa.Column('alerta', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove a coluna alerta
    op.drop_column('abordagem', 'alerta')
