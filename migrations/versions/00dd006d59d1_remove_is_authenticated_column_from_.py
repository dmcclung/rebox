"""Remove is_authenticated column from users table

Revision ID: 00dd006d59d1
Revises: d060f5ec3a65
Create Date: 2025-06-30 15:57:29.742044

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '00dd006d59d1'
down_revision = 'd060f5ec3a65'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c['name'] == column_name for c in columns)


def upgrade():
    # Only drop the column if it exists
    if column_exists('user', 'is_authenticated'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.drop_column('is_authenticated')


def downgrade():
    # Only add the column if it doesn't exist
    if not column_exists('user', 'is_authenticated'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_authenticated', sa.BOOLEAN(), autoincrement=False, nullable=True))
