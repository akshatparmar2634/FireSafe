"""Add fire detection fields to Feed

Revision ID: 1bb4b8ae7607
Revises: 
Create Date: 2025-04-05 22:17:37.343491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bb4b8ae7607'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('feed', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fire_detected', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('last_fire_detected_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=True))
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=80),
               existing_nullable=False)
        batch_op.alter_column('location',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=True)
        batch_op.alter_column('rtsp_url',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=300),
               existing_nullable=True)
        batch_op.drop_column('created_at')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('feed', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        batch_op.alter_column('rtsp_url',
               existing_type=sa.String(length=300),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
        batch_op.alter_column('location',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.String(length=80),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.drop_column('status')
        batch_op.drop_column('last_fire_detected_time')
        batch_op.drop_column('fire_detected')

    # ### end Alembic commands ###
