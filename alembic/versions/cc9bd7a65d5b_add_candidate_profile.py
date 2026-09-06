"""add candidate profile

Revision ID: cc9bd7a65d5b
Revises: d4dd98e44bd3
Create Date: 2026-08-18 18:38:02.701842

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = 'cc9bd7a65d5b'
down_revision: Union[str, Sequence[str], None] = 'd4dd98e44bd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # =========================
    # APPLICATION INDEXES
    # =========================

    op.create_index(
        op.f('ix_applications_job_id'),
        'applications',
        ['job_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_applications_resume_id'),
        'applications',
        ['resume_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_applications_status'),
        'applications',
        ['status'],
        unique=False
    )

    op.create_index(
        op.f('ix_applications_user_id'),
        'applications',
        ['user_id'],
        unique=False
    )

    # =========================
    # JOB SCHEMA SYNC
    # =========================

    op.alter_column(
        'jobs',
        'title',
        existing_type=mysql.VARCHAR(length=50),
        type_=sa.String(length=100),
        existing_nullable=False
    )

    op.alter_column(
        'jobs',
        'description',
        existing_type=mysql.VARCHAR(length=500),
        type_=sa.String(length=2000),
        existing_nullable=False
    )

    op.create_index(
        op.f('ix_jobs_company_id'),
        'jobs',
        ['company_id'],
        unique=False
    )

    op.create_index(
        op.f('ix_jobs_location'),
        'jobs',
        ['location'],
        unique=False
    )

    # =========================
    # RESUME INDEX
    # =========================

    op.create_index(
        op.f('ix_resumes_is_primary'),
        'resumes',
        ['is_primary'],
        unique=False
    )

    # =========================
    # CANDIDATE PROFILE
    # =========================

    op.create_table(
        'candidate_profiles',

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
            'headline',
            sa.String(length=150),
            nullable=True
        ),

        sa.Column(
            'bio',
            sa.String(length=1000),
            nullable=True
        ),

        sa.Column(
            'phone',
            sa.String(length=15),
            nullable=True
        ),

        sa.Column(
            'location',
            sa.String(length=100),
            nullable=True
        ),

        sa.Column(
            'experience_years',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'education',
            sa.String(length=500),
            nullable=True
        ),

        sa.Column(
            'skills',
            sa.JSON(),
            nullable=True
        ),

        sa.Column(
            'linkedin_url',
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            'github_url',
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            'portfolio_url',
            sa.String(length=255),
            nullable=True
        ),

        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False
        ),

        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),

        sa.PrimaryKeyConstraint('id'),

        sa.UniqueConstraint(
            'user_id',
            name='uq_candidate_profile_user'
        )
    )

    op.create_index(
        op.f('ix_candidate_profiles_id'),
        'candidate_profiles',
        ['id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    # =========================
    # CANDIDATE PROFILE
    # =========================

    op.drop_index(
        op.f('ix_candidate_profiles_id'),
        table_name='candidate_profiles'
    )

    op.drop_table(
        'candidate_profiles'
    )

    # =========================
    # RESUME INDEX
    # =========================

    op.drop_index(
        op.f('ix_resumes_is_primary'),
        table_name='resumes'
    )

    # =========================
    # JOB INDEXES
    # =========================

    op.drop_index(
        op.f('ix_jobs_location'),
        table_name='jobs'
    )

    op.drop_index(
        op.f('ix_jobs_company_id'),
        table_name='jobs'
    )

    # =========================
    # JOB SCHEMA
    # =========================

    op.alter_column(
        'jobs',
        'description',
        existing_type=sa.String(length=2000),
        type_=mysql.VARCHAR(length=500),
        existing_nullable=False
    )

    op.alter_column(
        'jobs',
        'title',
        existing_type=sa.String(length=100),
        type_=mysql.VARCHAR(length=50),
        existing_nullable=False
    )

    # =========================
    # APPLICATION INDEXES
    # =========================

    op.drop_index(
        op.f('ix_applications_user_id'),
        table_name='applications'
    )

    op.drop_index(
        op.f('ix_applications_status'),
        table_name='applications'
    )

    op.drop_index(
        op.f('ix_applications_resume_id'),
        table_name='applications'
    )

    op.drop_index(
        op.f('ix_applications_job_id'),
        table_name='applications'
    )