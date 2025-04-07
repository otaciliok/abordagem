"""adicionar campo alerta

Revision ID: adicionar_campo_alerta
Revises: f54fde9d0ef6
Create Date: 2025-04-05 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'adicionar_campo_alerta'
down_revision = 'f54fde9d0ef6'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna de alerta
    op.add_column('abordagem', sa.Column('alerta', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    # Remove a coluna de alerta
    op.drop_column('abordagem', 'alerta') 