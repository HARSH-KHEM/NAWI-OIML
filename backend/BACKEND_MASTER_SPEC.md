# SIH26035 Backend Master Specification (Version 1.0)

**Project:** OIML R-76 Type Evaluation Automation Platform (SIH26035)

**Architecture Owner:** Backend Team

**Frontend Consumer:** React Frontend

**Backend Stack:** FastAPI + PostgreSQL + SQLAlchemy + Alembic + Pydantic

---

# 1. Project Objective

Build a **deterministic backend platform** that digitizes the complete workflow of **OIML R-76 Non-Automatic Weighing Instrument (NAWI) Type Evaluation**.

The backend is **not** a CRUD application.

It is a **rule-driven evaluation engine** that:

* Generates evaluation plans based on instrument configuration.
* Guides laboratory testing.
* Stores immutable observations.
* Executes verified R-76 calculations.
* Determines compliance.
* Produces standardized reports.
* Maintains traceable evidence and history.

---

# 2. Core Backend Philosophy

These principles are **non-negotiable**.

## Principle 1 — Backend owns truth

Frontend never determines:

* Applicable tests.
* Maximum permissible error.
* PASS/FAIL.
* Compliance.
* Required observations.
* Rule applicability.

Frontend only renders backend responses.

---

## Principle 2 — Historical evaluations are immutable

An evaluation must always be reproducible using:

* Configuration snapshot.
* Rule version.
* Observations.
* Calculations.
* Compliance decisions.

Editing today's instrument configuration must never change yesterday's evaluation.

---

## Principle 3 — Applicability is different from Compliance

**Applicability**

> Which tests apply?

**Compliance**

> Did those tests pass?

These are implemented as separate engines.

---

## Principle 4 — Raw observations are evidence

Observations are never overwritten silently.

Everything derives from observations.

---

## Principle 5 — No AI decides compliance

PASS/FAIL is purely deterministic according to R-76.

AI may explain decisions later.

---

# 3. Complete Backend Workflow

```
Instrument
      │
      ▼
Instrument Configuration
      │
      ▼
Applicability Engine
      │
      ▼
Evaluation Plan
      │
      ▼
Guided Test Workflow
      │
      ▼
Observations
      │
      ▼
Validation Engine
      │
      ▼
Calculation Engine
      │
      ▼
Compliance Engine
      │
      ▼
Evidence Graph
      │
      ▼
Evaluation Summary
      │
      ▼
Report Generator
```

---

# 4. Tech Stack

| Layer              | Technology                          |
| ------------------ | ----------------------------------- |
| API                | FastAPI                             |
| Database           | PostgreSQL                          |
| ORM                | SQLAlchemy 2.x                      |
| Migration          | Alembic                             |
| Validation         | Pydantic                            |
| Testing            | Pytest                              |
| PDF                | WeasyPrint / ReportLab              |
| Decimal Arithmetic | Python Decimal + PostgreSQL NUMERIC |

---

# 5. Backend Folder Structure

```
backend/
│
├── app/
│
├── api/
│   ├── instruments.py
│   ├── evaluations.py
│   ├── tests.py
│   ├── observations.py
│   ├── reports.py
│   ├── evidence.py
│   └── auth.py
│
├── db/
│   ├── session.py
│   ├── base.py
│   └── migrations/
│
├── models/
│
├── schemas/
│
├── services/
│
├── engines/
│   ├── applicability.py
│   ├── workflow.py
│   ├── validation.py
│   ├── calculation.py
│   ├── compliance.py
│   ├── evidence.py
│   └── report.py
│
├── rules/
│
├── utils/
│
└── tests/
```

---

# 6. Database Design Philosophy

Database models **domain entities**, not UI screens.

Every evaluation forms a permanent historical record.

Avoid giant JSON blobs.

Avoid 50 tiny tables.

Use relational design with controlled JSON only where flexibility is required.

---

# 7. Complete Domain Model

```
User

Instrument
    │
InstrumentConfiguration
    │
Evaluation
    │
EvaluationTest
    │
TestAttempt
    │
TestPoint
    │
Observation
    │
Calculation
    │
ComplianceResult
    │
Evidence

Rule
RuleVersion

AuditEvent

Report
```

---

# 8. Entity Responsibilities

## Instrument

Persistent instrument identity.

Stores:

* Manufacturer
* Model
* Instrument family
* Prototype/Serial
* Current status

Does NOT store historical evaluation state.

---

## Instrument Configuration

Represents current metrological configuration.

Includes:

* Accuracy class
* Max
* Min
* e
* d
* Number of ranges
* Multiple range flag
* Tare support
* Electronic flag
* Zero-setting
* Other capabilities

---

## Configuration Snapshot

When an evaluation starts:

Create immutable snapshot.

Snapshot is linked permanently to evaluation.

Future edits create new snapshots.

---

## Evaluation

Represents one complete R-76 type evaluation.

Stores:

* Evaluation ID
* Configuration snapshot
* Rule version
* Operator
* Lab
* Status
* Created timestamp
* Completed timestamp

---

## EvaluationTest

One applicable R-76 test inside an evaluation.

Examples:

* Weighing Performance
* Eccentricity
* Repeatability
* Tare
* Zero-setting
* Temperature
* Voltage
* Endurance

Stores status independently.

---

## TestAttempt

Supports retries.

One EvaluationTest can have many attempts.

Attempt states:

* Attempt 1 FAIL
* Attempt 2 PASS

Never overwrite attempts.

---

## TestPoint (IMPORTANT)

Represents one logical measurement location within a test.

Supports:

### Weighing Performance

Many load points.

### Eccentricity

Multiple positions.

### Repeatability

Multiple readings grouped into series.

Fields conceptually include:

* sequence index
* point type
* position id
* series number
* target load
* status

This is mandatory for multi-point tests.

---

## Observation

Raw laboratory input.

Stores:

* Observation type
* Value
* Unit
* Entered by
* Timestamp

Examples:

Load = 10 kg

Indication = 10.004 kg

Temperature = 20°C

---

## Calculation

Stores deterministic calculated outputs.

Examples:

P

E

Ec

Mean

Deviation

Never stores observations.

References observations.

---

## ComplianceResult

Stores decision.

Values:

* PASS
* FAIL
* INCOMPLETE
* N_A

Includes:

* Criterion used.
* Rule version.
* Observed value.
* Limit value.

---

## Evidence

Traceability object.

Connects:

ComplianceResult

↓

Calculation

↓

Observation

↓

Test

↓

Evaluation

---

## Rule

Logical rule identity.

Examples:

R76-A4.4

R76-A4.7

R76-A4.10

---

## RuleVersion

Stores executable version of rule.

Includes:

* Standard version
* Clause
* Calculation identifier
* Applicability identifier
* Aggregation strategy

Historical evaluations reference specific RuleVersion.

---

## AuditEvent

Stores important actions.

Examples:

Evaluation created.

Observation modified.

Retest created.

Report generated.

---

## Report

Generated artifact metadata.

Includes:

* Report version.
* Generated timestamp.
* Evaluation reference.
* PDF location.

---

# 9. Applicability Engine (USP Engine)

## Purpose

Generate evaluation plan based on configuration.

## Input

Configuration snapshot.

Rule version.

## Output

Applicable tests.

Required observation templates.

Execution order.

Dependencies.

## Example

Multiple Range = NO

↓

Single-range workflow.

Multiple Range = YES

↓

Range-specific workflow.

This is the project's primary USP.

---

# 10. Workflow Engine

Converts evaluation plan into executable workflow.

Each test exposes:

* Steps.
* Required inputs.
* Instructions.
* Completion conditions.
* Validation metadata.

Frontend renders workflow returned by backend.

---

# 11. Validation Engine

Validation has four layers.

### Layer 1

Schema validation.

### Layer 2

Domain validation.

Example:

Min ≤ Max.

### Layer 3

Test completeness.

Required observations present.

### Layer 4

R-76 validation.

Observation constraints.

---

# 12. Calculation Engine

Implements verified R-76 formulas.

Prototype scope:

## Deep Implementations

### Weighing Performance

Implements official error calculations.

### Eccentricity

Per-position calculations.

### Repeatability

Series calculations.

Use Decimal.

Never float.

---

# 13. Aggregation Strategy

Multi-point tests require aggregation.

Examples:

ALL_POINTS_PASS

ANY_POINT_FAILS

MAX_ERROR_LIMIT

RANGE_WITHIN_LIMIT

Aggregation belongs to rule metadata.

Not frontend.

---

# 14. Compliance Engine

Consumes:

Calculated values.

Rule criteria.

Rule version.

Returns:

PASS / FAIL / INCOMPLETE / N_A

Includes reasoning metadata.

---

# 15. Evidence Engine

Builds trace graph.

```
Decision
   │
Criterion
   │
Rule Version
   │
Calculation
   │
Observation
   │
TestPoint
   │
TestAttempt
   │
Evaluation
```

Supports explainability.

---

# 16. Report Engine

Produces standardized R-76 report.

Pipeline:

Database

↓

Report Mapper

↓

PDF Template

↓

PDF Output

Never generates report directly from frontend.

---

# 17. Retest System

EvaluationTest supports many attempts.

History preserved.

Attempt timeline preserved.

Compliance preserved.

---

# 18. Audit System

Log:

* Evaluation creation.
* Configuration changes.
* Observation changes.
* Test completion.
* Compliance generation.
* Retest creation.
* Report generation.

---

# 19. API Design Principles

APIs expose domain operations.

Examples:

Generate Evaluation Plan.

Calculate Test.

Generate Report.

Retest.

Avoid exposing raw DB tables unnecessarily.

---

# 20. Core REST Endpoints

## Instruments

POST /instruments

GET /instruments

GET /instruments/{id}

PUT /instruments/{id}

---

## Evaluations

POST /evaluations

GET /evaluations/{id}

POST /evaluations/{id}/generate-plan

GET /evaluations/{id}/tests

---

## Tests

GET /tests/{id}

POST /tests/{id}/observations

POST /tests/{id}/calculate

POST /tests/{id}/retest

---

## Evidence

GET /evaluations/{id}/evidence

---

## Reports

POST /evaluations/{id}/generate-report

GET /reports/{id}

---

# 21. Security

Environment variables for secrets.

Input validation everywhere.

RBAC optional for prototype.

Frontend hiding buttons is not security.

---

# 22. Transactions

Atomic operations for:

Observation save.

Calculation.

Compliance creation.

Report generation.

Avoid partial database states.

---

# 23. Units Policy

Every observation stores explicit units.

Internal calculations normalize consistently.

---

# 24. Decimal Policy

All metrology calculations use Decimal.

Database uses NUMERIC.

Never FLOAT.

---

# 25. Seed Data

Create deterministic demo dataset.

Instrument A

↓

Evaluation PASS.

Instrument B

↓

Evaluation FAIL then PASS after retest.

Supports frontend demo immediately.

---

# 26. MUST / SHOULD / CUT

## MUST

Database schema.

Configuration snapshots.

Rule versioning.

Applicability Engine.

Evaluation Plan.

Weighing Performance.

Eccentricity.

Repeatability.

Compliance Engine.

Evidence trace.

PDF report.

---

## SHOULD

Audit log.

Instrument history.

Retests.

Evidence uploads.

Dashboard aggregation.

---

## CUT FIRST

Digital signatures.

DOCX export.

Admin rule editor.

AI assistant.

Advanced RBAC.

Cloud deployment.

---

# 27. Backend Testing Strategy

Unit Tests

Applicability.

Calculation.

Compliance.

Aggregation.

Integration Tests

Evaluation flow.

Retest flow.

Historical snapshots.

Regression Tests

Multiple Range configuration change.

Historical report reproduction.

---

# 28. Killer Demo Requirements

Scenario 1

Configuration A

Multiple Range = NO

↓

Generate Plan A.

Scenario 2

Configuration B

Multiple Range = YES

↓

Generate Plan B.

Plans must visibly differ.

Scenario 3

Run Weighing Performance.

PASS.

Scenario 4

Force FAIL.

Create Retest.

PASS.

Attempt history preserved.

Scenario 5

Generate report with evidence trace.

---

# 29. Things Antigravity MUST NOT Generate

* Business logic inside frontend assumptions.
* Generic CRUD-only backend.
* Float-based calculations.
* eval()-based formula execution.
* Giant JSON database blobs.
* Separate observation table for every R-76 test.
* AI-generated compliance logic.
* Mutable historical evaluations.

---

# 30. Development Order (Strict)

### Phase 1

Project setup.

Database.

Alembic.

Models.

Enums.

Seed data.

### Phase 2

Rule schema.

Applicability Engine.

Evaluation Plan API.

### Phase 3

Workflow Engine.

Observation APIs.

Validation Engine.

### Phase 4

Weighing Performance calculation.

Compliance Engine.

Unit tests.

### Phase 5

Eccentricity.

Repeatability.

Aggregation.

### Phase 6

Evidence.

Retest.

Audit.

Report generation.

### Phase 7

Frontend integration.

Regression tests.

Demo hardening.

---

# FINAL INSTRUCTION TO ANTIGRAVITY

Do NOT implement the entire backend in one generation.

Implement one phase at a time.

After each phase:

1. Generate models/services/APIs only for that phase.
2. Include SQLAlchemy models, Pydantic schemas, services and routes.
3. Include unit tests.
4. Wait for manual verification before implementing the next phase.

The architecture defined in this document is the source of truth and must not be redesigned unless explicitly instructed.
