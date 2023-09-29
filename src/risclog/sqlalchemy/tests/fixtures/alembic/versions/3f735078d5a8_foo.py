"""foo

Revision ID: 3f735078d5a8
Revises: None
Create Date: 2013-08-12 10:59:01.394646

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3f735078d5a8'
down_revision = None


def upgrade():
    op.create_table('foobar', sa.Column('id', sa.Integer()))


def downgrade():
    op.drop_table('foobar')  # pragma: no cover
