"""merge branches

Revision ID: d84cbf96b635
Revises: 634aca4653aa, add_converter_config
Create Date: 2025-05-07 02:17:39.506898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd84cbf96b635'
down_revision = ('634aca4653aa', 'add_converter_config')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
