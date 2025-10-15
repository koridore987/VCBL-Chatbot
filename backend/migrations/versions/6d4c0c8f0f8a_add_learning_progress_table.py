"""Add learning_progress table

Revision ID: 6d4c0c8f0f8a
Revises: bc741a1ffa94
Create Date: 2025-10-14 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression


# revision identifiers, used by Alembic.
revision = '6d4c0c8f0f8a'
down_revision = 'bc741a1ffa94'
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
    'learning_progress',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('video_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='not_started'),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('last_activity_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('survey_completed', sa.Boolean(), nullable=False, server_default=expression.false()),
    sa.Column('survey_completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), server_onupdate=sa.func.now()),
    sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    sa.ForeignKeyConstraint(['video_id'], ['videos.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'video_id', name='uq_learning_progress_user_video')
  )
  with op.batch_alter_table('learning_progress') as batch_op:
    batch_op.create_index(batch_op.f('ix_learning_progress_user_id'), ['user_id'], unique=False)
    batch_op.create_index(batch_op.f('ix_learning_progress_video_id'), ['video_id'], unique=False)


def downgrade():
  with op.batch_alter_table('learning_progress') as batch_op:
    batch_op.drop_index(batch_op.f('ix_learning_progress_video_id'))
    batch_op.drop_index(batch_op.f('ix_learning_progress_user_id'))
  op.drop_table('learning_progress')
