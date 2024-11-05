from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '148a1e34112d'
down_revision = '0e77067aa879'
branch_labels = None
depends_on = None


def upgrade():
    # Get the current connection
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    # Only create the 'teachers' table if it doesn't already exist
    if 'teachers' not in tables:
        op.create_table(
            'teachers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('subject', sa.String(length=50), nullable=False),
            sa.Column('hire_date', sa.DateTime(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )

    # Similarly, check for the 'admins' and 'finances' tables
    # if 'admins' not in tables:
    #     op.create_table(
    #         'admins',
    #         sa.Column('id', sa.Integer(), nullable=False),
    #         sa.Column('name', sa.String(length=100), nullable=False),
    #         sa.Column('hire_date', sa.DateTime(), nullable=True),
    #         sa.Column('user_id', sa.Integer(), nullable=True),
    #         sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    #         sa.PrimaryKeyConstraint('id'),
    #         sa.UniqueConstraint('user_id')
    #     )

    if 'finances' not in tables:
        op.create_table(
            'finances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('transaction_type', sa.String(length=50), nullable=False),
            sa.Column('date', sa.DateTime(), nullable=True),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['student_id'], ['students.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    # Add teacher_id column to students table if not already present
    with op.batch_alter_table('students', schema=None) as batch_op:
        if not any(column['name'] == 'teacher_id' for column in inspector.get_columns('students')):
            batch_op.add_column(sa.Column('teacher_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key("fk_student_teacher_id", 'teachers', ['teacher_id'], ['id'])


def downgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_constraint("fk_student_teacher_id", type_='foreignkey')
        batch_op.drop_column('teacher_id')

    op.drop_table('finances')
    op.drop_table('teachers')
    op.drop_table('admins')
