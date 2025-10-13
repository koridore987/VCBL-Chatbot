"""add_learning_enabled_to_video

Revision ID: 86216cd24f8a
Revises: 3c5bfb9b3352
Create Date: 2025-10-13 18:26:39.673387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86216cd24f8a'
down_revision = '3c5bfb9b3352'
branch_labels = None
depends_on = None


def upgrade():
    # learning_enabled 컬럼 추가 (기본값 False)
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('learning_enabled', sa.Boolean(), nullable=True))
    
    # 기존 데이터에 대해 기본값 설정
    op.execute('UPDATE videos SET learning_enabled = 0')
    
    # nullable=False로 변경
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.alter_column('learning_enabled', nullable=False)


def downgrade():
    # learning_enabled 컬럼 제거
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.drop_column('learning_enabled')
