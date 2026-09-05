"""Ugens fokus, ordbank og hjemmelæsningslog

Tre tabeller, der binder skole og hjemmelæsning sammen:

  weekly_focus     - lærerens fokus for en klasse i en uge, som følger
                     med hjem til Hjemmelæsning
  word_bank_entry  - de ordstammer, hvert barn har mødt
  home_reading_log - forælderens kvittering for, at der er læst

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'weekly_focus',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('aar', sa.Integer(), nullable=False),
        sa.Column('uge', sa.Integer(), nullable=False),
        sa.Column('lyde', sa.String(length=120), nullable=True),
        sa.Column('position', sa.String(length=20), nullable=False, server_default='forlyd'),
        sa.Column('fokusord', sa.Text(), nullable=True),
        sa.Column('besked_hjem', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classroom.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('classroom_id', 'aar', 'uge', name='uq_focus_klasse_uge'),
    )
    with op.batch_alter_table('weekly_focus', schema=None) as batch_op:
        batch_op.create_index('ix_weekly_focus_classroom_id', ['classroom_id'], unique=False)

    op.create_table(
        'word_bank_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stamme', sa.String(length=80), nullable=False),
        sa.Column('visningsform', sa.String(length=80), nullable=False),
        sa.Column('baand', sa.Integer(), nullable=True),
        sa.Column('antal_moeder', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('foerst_set', sa.DateTime(), nullable=True),
        sa.Column('sidst_set', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'stamme', name='uq_ordbank_bruger_stamme'),
    )
    with op.batch_alter_table('word_bank_entry', schema=None) as batch_op:
        batch_op.create_index('ix_word_bank_entry_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_word_bank_entry_stamme', ['stamme'], unique=False)

    op.create_table(
        'home_reading_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=True),
        sa.Column('dato', sa.Date(), nullable=False),
        sa.Column('minutter', sa.Integer(), nullable=True),
        sa.Column('laest_af', sa.String(length=20), nullable=True),
        sa.Column('kommentar', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['story.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('home_reading_log', schema=None) as batch_op:
        batch_op.create_index('ix_home_reading_log_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_home_reading_log_story_id', ['story_id'], unique=False)
        batch_op.create_index('ix_home_reading_log_dato', ['dato'], unique=False)


def downgrade():
    op.drop_table('home_reading_log')
    op.drop_table('word_bank_entry')
    op.drop_table('weekly_focus')
