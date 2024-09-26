"""added suppliers to invoices table

Revision ID: 566ad4d28559
Revises: 
Create Date: 2024-09-26 13:15:31.460894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '566ad4d28559'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Invoices', sa.Column('supplier_id', sa.Integer(), nullable=False))
    op.drop_column('Invoices', 'sender')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Invoices', sa.Column('sender', sa.VARCHAR(length=255), nullable=True))
    op.drop_column('Invoices', 'supplier_id')
    # ### end Alembic commands ###
