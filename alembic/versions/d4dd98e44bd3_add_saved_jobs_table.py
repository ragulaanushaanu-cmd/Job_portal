"""add saved jobs table

Revision ID: d4dd98e44bd3
Revises: f9a46f6bf932
Create Date: 2026-08-18 18:06:22.023263

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4dd98e44bd3'
down_revision: Union[str, Sequence[str], None] = 'f9a46f6bf932'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'saved_jobs',

        sa.Column(
            'id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'job_id',
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            'saved_at',
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),

        sa.ForeignKeyConstraint(
            ['job_id'],
            ['jobs.id'],
            ondelete='CASCADE'
        ),

        sa.PrimaryKeyConstraint('id'),

        sa.UniqueConstraint(
            'user_id',
            'job_id',
            name='uq_user_saved_job'
        )
    )

    op.create_index(
        op.f('ix_saved_jobs_id'),
        'saved_jobs',
        ['id'],
        unique=False
    )

    op.create_index(
        op.f('ix_saved_jobs_user_id'),
        'saved_jobs',
        ['user_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_saved_jobs_job_id'),
        'saved_jobs',
        ['job_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_saved_jobs_job_id'),
        table_name='saved_jobs'
    )

    op.drop_index(
        op.f('ix_saved_jobs_user_id'),
        table_name='saved_jobs'
    )

    op.drop_index(
        op.f('ix_saved_jobs_id'),
        table_name='saved_jobs'
    )

    op.drop_table('saved_jobs')