"""Convert prompts to persona system

Revision ID: 8e9f0d1a2b3c
Revises: 7a8b9c0d1e2f
Create Date: 2025-10-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e9f0d1a2b3c'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. is_global_active 컬럼이 없다면 추가 (이미 있을 수도 있음)
    with op.batch_alter_table('chat_prompt_templates', schema=None) as batch_op:
        # Try to add column, if it exists it will skip
        try:
            batch_op.add_column(sa.Column('is_global_active', sa.Boolean(), nullable=True, server_default='false'))
        except:
            pass  # Column might already exist
    
    # 2. 기존 데이터 마이그레이션
    # is_default=True인 프롬프트를 is_global_active=True로 변환
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE chat_prompt_templates SET is_global_active = TRUE WHERE is_default = TRUE")
    )
    
    # 3. 더 이상 사용하지 않는 컬럼 제거
    with op.batch_alter_table('chat_prompt_templates', schema=None) as batch_op:
        # Remove foreign key constraint for video_id first
        try:
            batch_op.drop_constraint('chat_prompt_templates_video_id_fkey', type_='foreignkey')
        except:
            pass  # Constraint might not exist
        
        # Drop columns
        batch_op.drop_column('video_id')
        batch_op.drop_column('user_role')
        batch_op.drop_column('is_default')


def downgrade():
    # Restore old columns
    with op.batch_alter_table('chat_prompt_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('video_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('user_role', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('is_default', sa.Boolean(), nullable=True))
        
        # Restore foreign key
        batch_op.create_foreign_key('chat_prompt_templates_video_id_fkey', 'videos', ['video_id'], ['id'])
    
    # Restore data: is_global_active=True -> is_default=True
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE chat_prompt_templates SET is_default = TRUE WHERE is_global_active = TRUE")
    )
    
    # Drop is_global_active column
    with op.batch_alter_table('chat_prompt_templates', schema=None) as batch_op:
        batch_op.drop_column('is_global_active')

