"""empty message

Revision ID: 915c25ffc69a
Revises: 9d00da11db0a
Create Date: 2022-05-11 09:41:26.452189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '915c25ffc69a'
down_revision = '9d00da11db0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comment', sa.Column('comment_id', sa.Integer(), nullable=True))
    op.add_column('comment', sa.Column('pic', sa.String(), nullable=True))
    op.create_foreign_key(None, 'comment', 'comment', ['comment_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comment', type_='foreignkey')
    op.drop_column('comment', 'pic')
    op.drop_column('comment', 'comment_id')
    # ### end Alembic commands ###
