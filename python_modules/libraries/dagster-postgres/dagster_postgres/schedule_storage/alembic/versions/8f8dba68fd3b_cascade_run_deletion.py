"""cascade run deletion

Revision ID: 8f8dba68fd3b
Revises: 567bc23fd1ac
Create Date: 2020-02-10 12:52:49.540462

"""
from alembic import op
from sqlalchemy.engine import reflection

# pylint: disable=no-member
# alembic dynamically populates the alembic.context module

# revision identifiers, used by Alembic.
revision = '8f8dba68fd3b'
down_revision = '567bc23fd1ac'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if 'runs' in has_tables and 'run_tags' in has_tables:
        op.drop_constraint('run_tags_run_id_fkey', table_name='run_tags', type='foreignkey')
        op.create_foreign_key(
            'run_tags_run_id_fkey',
            source_table='run_tags',
            referent_table='runs',
            local_cols=['run_id'],
            remote_cols=['run_id'],
            ondelete='CASCADE',
        )


def downgrade():
    bind = op.get_context().bind
    inspector = reflection.Inspector.from_engine(bind)
    has_tables = inspector.get_table_names()

    if 'runs' in has_tables and 'run_tags' in has_tables:
        op.drop_constraint('run_tags_run_id_fkey', table_name='run_tags', type='foreignkey')
        op.create_foreign_key(
            'run_tags_run_id_fkey',
            source_table='run_tags',
            referent_table='runs',
            local_cols=['run_id'],
            remote_cols=['run_id'],
        )
