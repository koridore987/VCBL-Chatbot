"""change_student_id_to_10digit_integer

Revision ID: 3c5bfb9b3352
Revises: da7b02980e30
Create Date: 2025-10-13 18:15:29.489983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c5bfb9b3352'
down_revision = 'da7b02980e30'
branch_labels = None
depends_on = None


def upgrade():
    # student_id를 String에서 BigInteger로 변경
    # password_hash를 nullable로 변경 (사전등록용)
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('student_id',
                              existing_type=sa.String(50),
                              type_=sa.BigInteger(),
                              nullable=False)
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(255),
                              nullable=True)


def downgrade():
    # Rollback: BigInteger를 String으로 되돌림
    # password_hash를 다시 not null로 변경
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('student_id',
                              existing_type=sa.BigInteger(),
                              type_=sa.String(50),
                              nullable=False)
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(255),
                              nullable=False)
