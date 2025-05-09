"""add converter_config table

Revision ID: add_converter_config
Revises: 23ea86c66706
Create Date: 2025-05-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_converter_config'
down_revision = '23ea86c66706'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'converter_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=256)),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('rules', sa.Text(), nullable=False),
        sa.Column('schema', sa.Text(), nullable=True),
    )

def downgrade():
    op.drop_table('converter_config') 