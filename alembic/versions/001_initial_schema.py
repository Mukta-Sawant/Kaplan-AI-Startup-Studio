"""Initial schema: submissions, agent_runs, phase_outputs, feedback_entries

Revision ID: 001
Revises:
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ENUM types: PostgreSQL has no CREATE TYPE IF NOT EXISTS syntax.
    # Use a DO block that catches duplicate_object and silently continues.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE startup_stage_enum AS ENUM
                ('idea', 'prototype', 'MVP', 'pilot', 'revenue');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE submission_status_enum AS ENUM
                ('submitted', 'clarification_needed',
                 'phase1_complete', 'mentor_review_required');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agent_run_status_enum AS ENUM
                ('success', 'failed', 'clarification_needed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE feedback_source_enum AS ENUM
                ('founder', 'mentor', 'admin');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE rerun_scope_enum AS ENUM
                ('eval', 'team', 'phase1');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # Tables use standard IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            startup_name          VARCHAR(255)           NOT NULL,
            one_line_pitch        VARCHAR(500)           NOT NULL,
            problem_statement     TEXT                   NOT NULL,
            proposed_solution     TEXT                   NOT NULL,
            target_market         TEXT                   NOT NULL,
            industry_vertical     VARCHAR(255)           NOT NULL,
            business_model        TEXT,
            traction_summary      TEXT,
            competitive_landscape TEXT,
            technical_status      TEXT,
            stage                 startup_stage_enum     NOT NULL,
            supporting_documents  JSONB,
            team_members          JSONB                  NOT NULL,
            status                submission_status_enum NOT NULL DEFAULT 'submitted',
            created_at            TIMESTAMPTZ            NOT NULL DEFAULT now(),
            updated_at            TIMESTAMPTZ            NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            submission_id         UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
            agent_name            VARCHAR(100)          NOT NULL,
            model_name            VARCHAR(200)          NOT NULL,
            version               VARCHAR(50)           NOT NULL DEFAULT '1.0.0',
            input_hash            VARCHAR(64)           NOT NULL,
            system_prompt_version VARCHAR(50)           NOT NULL,
            input_payload         JSONB                 NOT NULL,
            output_json           JSONB,
            coherence_score       FLOAT,
            confidence_level      FLOAT,
            run_status            agent_run_status_enum NOT NULL DEFAULT 'success',
            created_at            TIMESTAMPTZ           NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_agent_runs_submission_id
            ON agent_runs(submission_id)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS phase_outputs (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            submission_id          UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
            phase_name             VARCHAR(100) NOT NULL,
            merged_output          JSONB        NOT NULL,
            mentor_review_required BOOLEAN      NOT NULL DEFAULT false,
            created_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_phase_outputs_submission_id
            ON phase_outputs(submission_id)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS feedback_entries (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            submission_id  UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
            source_type    feedback_source_enum NOT NULL,
            feedback_text  TEXT                 NOT NULL,
            triggers_rerun BOOLEAN              NOT NULL DEFAULT false,
            rerun_scope    rerun_scope_enum,
            created_at     TIMESTAMPTZ          NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_feedback_entries_submission_id
            ON feedback_entries(submission_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS feedback_entries")
    op.execute("DROP TABLE IF EXISTS phase_outputs")
    op.execute("DROP TABLE IF EXISTS agent_runs")
    op.execute("DROP TABLE IF EXISTS submissions")
    op.execute("DROP TYPE IF EXISTS rerun_scope_enum")
    op.execute("DROP TYPE IF EXISTS feedback_source_enum")
    op.execute("DROP TYPE IF EXISTS agent_run_status_enum")
    op.execute("DROP TYPE IF EXISTS submission_status_enum")
    op.execute("DROP TYPE IF EXISTS startup_stage_enum")
