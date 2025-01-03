"""update student

Revision ID: 66c05038ba23
Revises: d3b488ae3881
Create Date: 2024-12-26 13:52:36.828441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66c05038ba23'
down_revision = 'd3b488ae3881'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('middle_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=100), nullable=True))
        batch_op.drop_constraint('students_teacher_id_fkey', type_='foreignkey')
        batch_op.drop_column('teacher_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('teacher_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('students_teacher_id_fkey', 'teachers', ['teacher_id'], ['id'])
        batch_op.drop_column('last_name')
        batch_op.drop_column('middle_name')
        batch_op.drop_column('first_name')

    # ### end Alembic commands ###
