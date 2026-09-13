"""Phase 1 initial database schema migration.

Revision ID: 0001_phase1_initial
Revises: 
Create Date: 2026-09-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_phase1_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="OPERATOR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. instruments table
    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("instrument_family", sa.String(length=100), nullable=False, server_default="NAWI"),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_instruments_manufacturer", "instruments", ["manufacturer"])
    op.create_index("ix_instruments_model_name", "instruments", ["model_name"])
    op.create_index("ix_instruments_serial_number", "instruments", ["serial_number"])
    op.create_index("ix_instruments_is_synthetic", "instruments", ["is_synthetic"])
    op.create_index("ix_instruments_manufacturer_model", "instruments", ["manufacturer", "model_name"])

    # 3. instrument_configurations table
    op.create_table(
        "instrument_configurations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("instrument_id", sa.Uuid(as_uuid=True), sa.ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accuracy_class", sa.String(length=64), nullable=False),
        sa.Column("max_capacity", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("min_capacity", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("verification_scale_interval", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("actual_scale_interval", sa.Numeric(precision=20, scale=6, asdecimal=True), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False, server_default="kg"),
        sa.Column("number_of_ranges", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_multiple_range", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tare_type", sa.String(length=64), nullable=False, server_default="SUBTRACTIVE"),
        sa.Column("is_electronic", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("has_zero_setting", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("extra_capabilities", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("min_capacity > 0", name="check_min_capacity_positive"),
        sa.CheckConstraint("max_capacity > 0", name="check_max_capacity_positive"),
        sa.CheckConstraint("min_capacity <= max_capacity", name="check_min_lte_max"),
        sa.CheckConstraint("actual_scale_interval <= verification_scale_interval", name="check_d_lte_e"),
        sa.CheckConstraint("number_of_ranges >= 1", name="check_number_of_ranges_gte_1"),
    )
    op.create_index("ix_instrument_configurations_instrument_id", "instrument_configurations", ["instrument_id"])

    # 4. rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rules_code", "rules", ["code"], unique=True)

    # 5. rule_versions table
    op.create_table(
        "rule_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("rule_id", sa.Uuid(as_uuid=True), sa.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.String(length=64), nullable=False),
        sa.Column("standard_version", sa.String(length=128), nullable=False),
        sa.Column("clause", sa.String(length=64), nullable=False),
        sa.Column("calculation_identifier", sa.String(length=128), nullable=False),
        sa.Column("applicability_identifier", sa.String(length=128), nullable=False),
        sa.Column("aggregation_strategy", sa.String(length=64), nullable=False, server_default="ALL_POINTS_PASS"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rule_id", "version_number", name="uq_rule_versions_rule_version"),
    )
    op.create_index("ix_rule_versions_rule_id", "rule_versions", ["rule_id"])

    # 6. evaluations table
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("evaluation_number", sa.String(length=64), nullable=False),
        sa.Column("instrument_id", sa.Uuid(as_uuid=True), sa.ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("instrument_configuration_id", sa.Uuid(as_uuid=True), sa.ForeignKey("instrument_configurations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rule_version_id", sa.Uuid(as_uuid=True), sa.ForeignKey("rule_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("configuration_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("operator_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lab_name", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluations_evaluation_number", "evaluations", ["evaluation_number"], unique=True)
    op.create_index("ix_evaluations_instrument_id", "evaluations", ["instrument_id"])
    op.create_index("ix_evaluations_instrument_configuration_id", "evaluations", ["instrument_configuration_id"])
    op.create_index("ix_evaluations_rule_version_id", "evaluations", ["rule_version_id"])
    op.create_index("ix_evaluations_operator_id", "evaluations", ["operator_id"])
    op.create_index("ix_evaluations_status", "evaluations", ["status"])


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_table("rule_versions")
    op.drop_table("rules")
    op.drop_table("instrument_configurations")
    op.drop_table("instruments")
    op.drop_table("users")
