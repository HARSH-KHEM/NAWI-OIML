"""Safe development seed script for synthetic demo fixtures (Phase 2).

Inserts canonical test definitions, standard OIML R-76 rules with content hash,
and synthetic single-range and multi-range demo instruments.
All demo instruments are explicitly flagged with `is_synthetic=True` and clearly
annotated to prevent any accidental misrepresentation as real approved instruments.
"""

from decimal import Decimal
import hashlib
import json
import logging
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.configuration import AccuracyClass, InstrumentConfiguration, TareType
from app.models.instrument import Instrument, InstrumentStatus
from app.models.range import InstrumentConfigurationRange
from app.models.rule import Rule, RuleVersion
from app.models.test_definition import ImplementationStatus, ScopeType, TestDefinition
from app.models.user import User, UserRole
from app.services.plan_service import ensure_test_definitions

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def compute_rule_content_hash(rule_def: dict) -> str:
    """Compute deterministic SHA-256 hash of canonicalized JSON rule definition."""
    canonical_json = json.dumps(rule_def, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def seed_synthetic_data(db: Optional[Session] = None) -> dict:
    """Seed canonical test definitions, rule versions, and synthetic demo instruments."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # 1. Ensure canonical test definitions exist
        defs_by_code = ensure_test_definitions(db)
        logger.info("Verified %d canonical R-76 test definitions in catalog", len(defs_by_code))

        # 2. Seed or fetch demo admin/operator user
        admin_user = db.scalar(
            select(User).where(User.email == "demo.operator@metrology.local")
        )
        if not admin_user:
            admin_user = User(
                email="demo.operator@metrology.local",
                full_name="Demo Lab Operator (Synthetic)",
                role=UserRole.OPERATOR,
                is_active=True,
            )
            db.add(admin_user)
            db.flush()
            logger.info("Created synthetic demo operator: %s", admin_user.email)

        # 3. Seed standard OIML R-76 Rule and RuleVersion with content hash
        rule = db.scalar(select(Rule).where(Rule.code == "OIML-R76-2006"))
        if not rule:
            rule = Rule(
                code="OIML-R76-2006",
                name="OIML R 76-1: Non-automatic weighing instruments",
                description="International standard defining metrological requirements and testing procedures.",
            )
            db.add(rule)
            db.flush()
            logger.info("Created rule: %s", rule.code)

        rule_def_dict = {
            "standard": "OIML R 76-1: 2006 (E)",
            "version": "2006-01",
            "tests": {
                "WEIGHING_PERFORMANCE": {
                    "clause": "A.4.4.3",
                    "calculation_identifier": "R76_A4_4_3_ERROR",
                    "criterion": {"type": "ABS_LE_MPE"},
                    "mpe": {"source": "TABLE_6"},
                },
                "ECCENTRICITY": {
                    "clause": "A.4.7",
                    "calculation_identifier": "R76_ECCENTRICITY",
                    "criterion": {"type": "MAX_POS_ABS_LE_MPE"},
                    "mpe": {"source": "TABLE_6"},
                },
                "REPEATABILITY": {
                    "clause": "A.4.10",
                    "calculation_identifier": "R76_REPEATABILITY",
                    "criterion": {"type": "SPAN_LE_MPE"},
                    "mpe": {"source": "TABLE_6"},
                },
            },
            "clauses": {
                "A.4.4.3": {"formula": "P = I + 0.5e - ΔL", "error": "E = P - L", "corrected_error": "Ec = E - E0"},
                "3.5.1": {"table": "Table 6", "criterion": "abs(Ec) <= mpe"},
                "A.4.7": {"title": "Eccentricity", "criterion": "abs(Ec_pos) <= mpe"},
                "A.4.10": {"title": "Repeatability", "criterion": "max(E) - min(E) <= mpe"},
                "3.9.4.3": {"title": "Endurance", "condition": "classes in (II, III, IIII) and Max <= 100 kg"},
            },
        }
        content_hash = compute_rule_content_hash(rule_def_dict)

        rule_version = db.scalar(
            select(RuleVersion).where(
                RuleVersion.rule_id == rule.id,
                RuleVersion.version_number == "2006-01",
            )
        )
        if not rule_version:
            rule_version = RuleVersion(
                rule_id=rule.id,
                version_number="2006-01",
                standard_version="OIML R 76-1: 2006 (E)",
                clause="Metrological Requirements & Technical Tests",
                calculation_identifier="R76_CALC_STANDARD_2006",
                applicability_identifier="R76_APP_STANDARD_2006",
                aggregation_strategy="ALL_POINTS_PASS",
                definition_json=rule_def_dict,
                content_hash=content_hash,
                is_active=True,
            )
            db.add(rule_version)
            db.flush()
            logger.info("Created rule version: %s - %s (hash: %s)", rule.code, rule_version.version_number, content_hash[:12])
        else:
            rule_version.definition_json = rule_def_dict
            rule_version.content_hash = content_hash
            db.flush()

        # 4. Primary Demo Instrument: Synthetic Class III Single-Range NAWI (Max = 30 kg, e = 0.01 kg)
        demo_inst_single = db.scalar(
            select(Instrument).where(
                Instrument.serial_number == "SYNTH-DEMO-NAWI-001-SN"
            )
        )
        if not demo_inst_single:
            demo_inst_single = Instrument(
                manufacturer="[SYNTHETIC] Global Bench Metrology Systems",
                model_name="SYNTH-DEMO-NAWI-001",
                instrument_family="NAWI",
                serial_number="SYNTH-DEMO-NAWI-001-SN",
                status=InstrumentStatus.ACTIVE,
                is_synthetic=True,  # Mandatory synthetic guardrail
            )
            db.add(demo_inst_single)
            db.flush()
            logger.info("Created synthetic single-range instrument: %s", demo_inst_single.model_name)

        config_single = db.scalar(
            select(InstrumentConfiguration).where(
                InstrumentConfiguration.instrument_id == demo_inst_single.id
            )
        )
        if not config_single:
            # Class III: Max 30 kg, Min 0.2 kg, e = 0.01 kg, d = 0.01 kg
            config_single = InstrumentConfiguration(
                instrument_id=demo_inst_single.id,
                accuracy_class=AccuracyClass.CLASS_III,
                max_capacity=Decimal("30.000"),
                min_capacity=Decimal("0.200"),
                verification_scale_interval=Decimal("0.010"),
                actual_scale_interval=Decimal("0.010"),
                unit="kg",
                number_of_ranges=1,
                is_multiple_range=False,
                tare_type=TareType.SUBTRACTIVE,
                is_electronic=True,
                has_zero_setting=True,
                extra_capabilities={
                    "synthetic_fixture": True,
                    "type": "Single-Range Bench Scale",
                    "load_receptor": {
                        "support_count": 4,
                        "special_receptor": False,
                        "rolling_load": False,
                    },
                },
                is_active=True,
            )
            db.add(config_single)
            db.flush()
            logger.info("Created configuration for single-range instrument: Max=%s%s, e=%s%s", config_single.max_capacity, config_single.unit, config_single.verification_scale_interval, config_single.unit)

        # 5. Second Demo Instrument: Synthetic Class III Multiple-Range NAWI
        # Range 1: Max = 15 kg, Min = 0.2 kg, e = 0.005 kg, d = 0.005 kg
        # Range 2: Max = 30 kg, Min = 0.2 kg, e = 0.010 kg, d = 0.010 kg
        demo_inst_multi = db.scalar(
            select(Instrument).where(
                Instrument.serial_number == "SYNTH-DEMO-MULTI-002-SN"
            )
        )
        if not demo_inst_multi:
            demo_inst_multi = Instrument(
                manufacturer="[SYNTHETIC] Global Bench Metrology Systems",
                model_name="SYNTH-DEMO-MULTI-002",
                instrument_family="NAWI",
                serial_number="SYNTH-DEMO-MULTI-002-SN",
                status=InstrumentStatus.ACTIVE,
                is_synthetic=True,
            )
            db.add(demo_inst_multi)
            db.flush()
            logger.info("Created synthetic multi-range instrument: %s", demo_inst_multi.model_name)

        config_multi = db.scalar(
            select(InstrumentConfiguration).where(
                InstrumentConfiguration.instrument_id == demo_inst_multi.id
            )
        )
        if not config_multi:
            config_multi = InstrumentConfiguration(
                instrument_id=demo_inst_multi.id,
                accuracy_class=AccuracyClass.CLASS_III,
                max_capacity=Decimal("30.000"),
                min_capacity=Decimal("0.200"),
                verification_scale_interval=Decimal("0.010"),
                actual_scale_interval=Decimal("0.010"),
                unit="kg",
                number_of_ranges=2,
                is_multiple_range=True,
                tare_type=TareType.SUBTRACTIVE,
                is_electronic=True,
                has_zero_setting=True,
                extra_capabilities={
                    "synthetic_fixture": True,
                    "type": "Multi-Range Retail Scale",
                    "load_receptor": {
                        "support_count": 4,
                        "special_receptor": False,
                        "rolling_load": False,
                    },
                },
                is_active=True,
            )
            db.add(config_multi)
            db.flush()

            range1 = InstrumentConfigurationRange(
                configuration_id=config_multi.id,
                range_index=1,
                min_capacity=Decimal("0.200"),
                max_capacity=Decimal("15.000"),
                verification_scale_interval=Decimal("0.005"),
                actual_scale_interval=Decimal("0.005"),
                unit="kg",
            )
            range2 = InstrumentConfigurationRange(
                configuration_id=config_multi.id,
                range_index=2,
                min_capacity=Decimal("0.200"),
                max_capacity=Decimal("30.000"),
                verification_scale_interval=Decimal("0.010"),
                actual_scale_interval=Decimal("0.010"),
                unit="kg",
            )
            db.add_all([range1, range2])
            db.flush()
            logger.info("Created multi-range configuration with 2 ranges for %s", demo_inst_multi.model_name)

        db.commit()
        logger.info("✅ Phase 2 safe synthetic development seed completed successfully.")
        return {
            "instrument_id": str(demo_inst_single.id),
            "configuration_id": str(config_single.id),
            "single_range_instrument_id": str(demo_inst_single.id),
            "multi_range_instrument_id": str(demo_inst_multi.id),
            "single_range_config_id": str(config_single.id),
            "multi_range_config_id": str(config_multi.id),
            "rule_id": str(rule.id),
            "rule_version_id": str(rule_version.id),
        }
    except Exception as exc:
        db.rollback()
        logger.error("Error during Phase 2 synthetic seeding: %s", exc)
        raise
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    logger.info("Seeding Phase 2 canonical data into PostgreSQL...")
    seed_synthetic_data()
