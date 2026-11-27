"""add feature 2 asset fields and feature 3 risk fields

Revision ID: a1b2c3d4e5f6
Revises: e00b4bef20ac
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'e00b4bef20ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Feature 2: Asset fields ──
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(50), nullable=False, server_default='general'))
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_assets_owner_id', ['owner_id'])
        batch_op.create_foreign_key('fk_assets_owner_id_users', 'users', ['owner_id'], ['id'])

    # ── Feature 3: Risk fields ──
    with op.batch_alter_table('risks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('evidence', sa.Text(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('remediation_notes', sa.Text(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        batch_op.create_index('ix_risks_assignee_id', ['assignee_id'])
        batch_op.create_foreign_key('fk_risks_assignee_id_users', 'users', ['assignee_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('risks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_risks_assignee_id_users', type_='foreignkey')
        batch_op.drop_index('ix_risks_assignee_id')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('remediation_notes')
        batch_op.drop_column('evidence')
        batch_op.drop_column('assignee_id')

    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.drop_constraint('fk_assets_owner_id_users', type_='foreignkey')
        batch_op.drop_index('ix_assets_owner_id')
        batch_op.drop_column('owner_id')
        batch_op.drop_column('category')
