"""Tilføj indekser på de kolonner der filtreres og sorteres på

Logbogen slår op på (user_id, is_log_entry) og sorterer på created_at.
Klasseværelset slår op pr. elev og pr. klasse. Uden indekser laver
databasen et fuldt tabelscan for hver af de forespørgsler.

Revision ID: a1b2c3d4e5f6
Revises: 04c6f85ffc86
Create Date: 2026-09-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '04c6f85ffc86'
branch_labels = None
depends_on = None


# (tabel, indeksnavn, kolonner)
INDEXES = [
    ('story', 'ix_story_user_id', ['user_id']),
    ('story', 'ix_story_created_at', ['created_at']),
    ('story', 'ix_story_is_log_entry', ['is_log_entry']),
    ('story', 'ix_story_parent_story_id', ['parent_story_id']),
    ('story', 'ix_story_root_story_id', ['root_story_id']),
    ('child_profile', 'ix_child_profile_user_id', ['user_id']),
    ('profile_attribute', 'ix_profile_attribute_profile_id', ['profile_id']),
    ('profile_relation', 'ix_profile_relation_profile_id', ['profile_id']),
    ('classroom', 'ix_classroom_teacher_id', ['teacher_id']),
    ('classroom_student', 'ix_classroom_student_classroom_id', ['classroom_id']),
    ('classroom_student', 'ix_classroom_student_student_user_id', ['student_user_id']),
    ('quiz_result', 'ix_quiz_result_user_id', ['user_id']),
    ('quiz_result', 'ix_quiz_result_story_id', ['story_id']),
]


def upgrade():
    for table, name, columns in INDEXES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.create_index(name, columns, unique=False)


def downgrade():
    for table, name, _columns in reversed(INDEXES):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_index(name)
