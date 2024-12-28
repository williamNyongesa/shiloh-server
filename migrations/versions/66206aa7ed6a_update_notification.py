"""update notification

Revision ID: 66206aa7ed6a
Revises: c6bfa1fc10f2
Create Date: 2024-12-26 09:35:12.075907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66206aa7ed6a'
down_revision = 'c6bfa1fc10f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notifications')
    # ### end Alembic commands ###
