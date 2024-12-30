"""updating teachers foreign key

Revision ID: 6ecc104c0769
Revises: 964c92644ca3
Create Date: 2024-12-27 02:15:08.211339

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ecc104c0769'
down_revision = '964c92644ca3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('teacher_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'teachers', ['teacher_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('teacher_id')

    # ### end Alembic commands ###
