"""Phase 2 R-76 metrological engine schema migration.

Revision ID: 0002_phase2_r76_engine
Revises: 0001_phase1_initial
Create Date: 2026-09-13 12:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_phase2_r76_engine"
down_revision: Union[str, None] = "0001_phase1_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend rule_versions table
    op.add_column(
        "rule_versions",
        sa.Column("definition_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "rule_versions",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "rule_versions",
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. instrument_configuration_ranges table
    op.create_table(
        "instrument_configuration_ranges",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "configuration_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("instrument_configurations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("range_index", sa.Integer(), nullable=False),
        sa.Column("max_capacity", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("min_capacity", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("verification_scale_interval", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("actual_scale_interval", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False, server_default="kg"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("range_index >= 1", name="check_range_index_gte_1"),
        sa.CheckConstraint("min_capacity > 0", name="check_range_min_capacity_positive"),
        sa.CheckConstraint("max_capacity > 0", name="check_range_max_capacity_positive"),
        sa.CheckConstraint("min_capacity <= max_capacity", name="check_range_min_lte_max"),
        sa.CheckConstraint("actual_scale_interval <= verification_scale_interval", name="check_range_d_lte_e"),
    )
    op.create_index(
        "ix_instrument_configuration_ranges_configuration_id",
        "instrument_configuration_ranges",
        ["configuration_id"],
    )

    # 3. test_definitions table
    op.create_table(
        "test_definitions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("test_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("r76_reference", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("implementation_status", sa.String(length=32), nullable=False, server_default="APPLICABILITY_ONLY"),
        sa.Column("scope_type", sa.String(length=32), nullable=False, server_default="INSTRUMENT"),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_test_definitions_test_code", "test_definitions", ["test_code"], unique=True)

    # 4. evaluation_tests table
    op.create_table(
        "evaluation_tests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "test_definition_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_definitions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rule_version_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("rule_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="NOT_STARTED"),
        sa.Column("scope_type", sa.String(length=32), nullable=False, server_default="INSTRUMENT"),
        sa.Column("range_reference", sa.String(length=64), nullable=True),
        sa.Column("range_index", sa.Integer(), nullable=True),
        sa.Column("applicability_reason", sa.String(length=500), nullable=False),
        sa.Column("implementation_status", sa.String(length=64), nullable=False, server_default="IMPLEMENTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_tests_evaluation_id", "evaluation_tests", ["evaluation_id"])
    op.create_index("ix_evaluation_tests_test_definition_id", "evaluation_tests", ["test_definition_id"])
    op.create_index("ix_evaluation_tests_rule_version_id", "evaluation_tests", ["rule_version_id"])
    op.create_index("ix_evaluation_tests_status", "evaluation_tests", ["status"])

    # 5. test_attempts table
    op.create_table(
        "test_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "evaluation_test_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evaluation_tests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "supersedes_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_test_attempts_evaluation_test_id", "test_attempts", ["evaluation_test_id"])
    op.create_index("ix_test_attempts_status", "test_attempts", ["status"])

    # 6. test_steps table
    op.create_table(
        "test_steps",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "test_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_code", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instruction", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_test_steps_test_attempt_id", "test_steps", ["test_attempt_id"])

    # 7. observations table
    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "test_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "test_step_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_steps.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("observation_code", sa.String(length=64), nullable=False),
        sa.Column("value_numeric", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=True),
        sa.Column("value_text", sa.String(length=255), nullable=True),
        sa.Column("unit", sa.String(length=16), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("entered_by", sa.String(length=255), nullable=True),
        sa.Column("validation_status", sa.String(length=32), nullable=False, server_default="VALID"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_observations_test_attempt_id", "observations", ["test_attempt_id"])
    op.create_index("ix_observations_test_step_id", "observations", ["test_step_id"])

    # 8. calculations table
    op.create_table(
        "calculations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "test_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("calculation_code", sa.String(length=64), nullable=False),
        sa.Column("input_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("formula_reference", sa.String(length=128), nullable=False),
        sa.Column(
            "rule_version_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("rule_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_calculations_test_attempt_id", "calculations", ["test_attempt_id"])
    op.create_index("ix_calculations_rule_version_id", "calculations", ["rule_version_id"])

    # 9. compliance_results table
    op.create_table(
        "compliance_results",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "test_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "calculation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("calculations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("criterion_value", sa.String(length=128), nullable=False),
        sa.Column("measured_value", sa.String(length=128), nullable=False),
        sa.Column("margin", sa.String(length=128), nullable=True),
        sa.Column(
            "rule_version_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("rule_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reasoning_json", sa.JSON(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_compliance_results_test_attempt_id", "compliance_results", ["test_attempt_id"])
    op.create_index("ix_compliance_results_calculation_id", "compliance_results", ["calculation_id"])
    op.create_index("ix_compliance_results_rule_version_id", "compliance_results", ["rule_version_id"])
    op.create_index("ix_compliance_results_decision", "compliance_results", ["decision"])

    # 10. evidence table
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evaluations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "test_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("test_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "observation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("observations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "calculation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("calculations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_evaluation_id", "evidence", ["evaluation_id"])
    op.create_index("ix_evidence_test_attempt_id", "evidence", ["test_attempt_id"])
    op.create_index("ix_evidence_observation_id", "evidence", ["observation_id"])
    op.create_index("ix_evidence_calculation_id", "evidence", ["calculation_id"])

    # 11. audit_events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "evaluation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("evaluations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_evaluation_id", "audit_events", ["evaluation_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("evidence")
    op.drop_table("compliance_results")
    op.drop_table("calculations")
    op.drop_table("observations")
    op.drop_table("test_steps")
    op.drop_table("test_attempts")
    op.drop_table("evaluation_tests")
    op.drop_table("test_definitions")
    op.drop_table("instrument_configuration_ranges")
    op.drop_column("rule_versions", "effective_from")
    op.drop_column("rule_versions", "content_hash")
    op.drop_column("rule_versions", "definition_json")
