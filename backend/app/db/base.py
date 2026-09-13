"""Central Base metadata registry for SQLAlchemy and Alembic.

Importing this module ensures that all model classes are registered
in Base.metadata before migrations or table creations run.
"""

from app.models.base import Base, CommonBaseModel
from app.models.configuration import InstrumentConfiguration
from app.models.evaluation import Evaluation
from app.models.instrument import Instrument
from app.models.metrology import AuditEvent, Calculation, ComplianceResult, Evidence
from app.models.range import InstrumentConfigurationRange
from app.models.rule import Rule, RuleVersion
from app.models.test_definition import TestDefinition
from app.models.test_execution import EvaluationTest, Observation, TestAttempt, TestStep
from app.models.user import User

__all__ = [
    "Base",
    "CommonBaseModel",
    "User",
    "Instrument",
    "InstrumentConfiguration",
    "InstrumentConfigurationRange",
    "Rule",
    "RuleVersion",
    "Evaluation",
    "TestDefinition",
    "EvaluationTest",
    "TestAttempt",
    "TestStep",
    "Observation",
    "Calculation",
    "ComplianceResult",
    "Evidence",
    "AuditEvent",
]
