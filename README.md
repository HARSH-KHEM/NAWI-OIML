# NAWI-OIML

### SIH26035 — NAWI OIML R-76 Type Evaluation Platform

---

## Project Overview

**NAWI-OIML** is a software platform developed for **SIH26035** to digitize, automate, and structure the type-evaluation workflow for **Non-Automatic Weighing Instruments (NAWIs)** under the international standard **OIML R 76-1:2006 (E)** and **OIML R 76-2:2007 (E)**.

In legal metrology, NAWI type evaluation evaluates whether an instrument design complies with rigorous metrological and technical specifications before commercial verification and market release. Traditionally, this process relies on manual record-keeping, static spreadsheets, and ad-hoc calculations, which increases the risk of transcription errors and impairs auditability.

**NAWI-OIML** is architected to:
- **Capture instrument configuration and technical parameters** (accuracy class, capacity boundaries, scale intervals, range structures, load-receptor geometry).
- **Derive applicable R-76 evaluation procedures** dynamically from instrument metadata.
- **Guide laboratory observations** via generated, step-by-step test plans.
- **Perform deterministic metrological calculations** with arbitrary-precision Decimal arithmetic.
- **Evaluate compliance against configured R-76 criteria** and maximum permissible error (MPE) envelopes.
- **Preserve immutable evidence and an append-only audit history** across test attempts and recalibrations.
- **Generate a fully traceable evaluation record** linking decisions back to raw laboratory observations and frozen configurations.

> **Notice:** This software is an engineering prototype developed for SIH26035. It does not claim official OIML certification, endorsement, or statutory legal-metrology approval.

---

## Core USP

> **"Configuration-driven executable R-76 evaluation workflow."**

Rather than functioning as a disconnected formula calculator, NAWI-OIML dynamically compiles an instrument's metrological configuration into an executable, laboratory-ready test plan:

```
Instrument Configuration
        ↓
Applicability Engine
        ↓
Configuration-dependent R-76 Procedure
        ↓
Executable Test Plan
        ↓
Validated Observations
        ↓
Deterministic Calculation
        ↓
MPE / Compliance Criterion
        ↓
PASS / FAIL / INCOMPLETE
        ↓
Evidence / Audit Trace
```

By binding R-76 logic directly to the instrument's characteristics (e.g., single-range vs. multi-range, 4-point vs. multi-support platforms, rolling loads), the platform eliminates procedural guesswork for laboratory technicians and prevents invalid testing sequences.

---

## Current Implemented Deep Procedures

The Phase 2 checkpoint implements deep, authoritative mathematical execution and MPE compliance engines for three primary OIML R-76 tests:

### 1. Weighing Performance (OIML R 76-1:2006 Clause A.4.4 & A.4.4.3)
- Evaluates errors across the operational weighing range (Class I, II, III, IIII).
- Uses exact turning-point formulas with auxiliary loads ($\Delta L$):
  $$P = I + 0.5e - \Delta L$$
  $$E = P - L$$
  $$E_c = E - E_0$$
- Evaluates $|E_c| \le MPE$ according to Table 6 limits based on load ratio $m/e$.

### 2. Eccentricity (OIML R 76-1:2006 Clause A.4.7)
- Selects the correct evaluation procedure based on load-receptor geometry.
- Derives the exact test load via Decimal arithmetic:
  $$\text{load} = \frac{Max + \text{additive\_tare}}{3} \quad \left(\text{or } \frac{Max}{N - 1} \text{ for } N > 4\right)$$
- Enforces strict load tolerance ($\pm 2\%$) and rejects calculations from incorrect loads.
- Evaluates maximum absolute corrected error across all positions against the applicable MPE.

### 3. Repeatability (OIML R 76-1:2006 Clause A.4.10)
- Implements the type-evaluation dual-series protocol:
  - **Series 1:** Load $\approx 50\% Max$
  - **Series 2:** Load $\approx 100\% Max$
- Enforces minimum observation counts ($n \ge 10$ for $Max < 1000\text{ kg}$; $n \ge 3$ for $Max \ge 1000\text{ kg}$).
- Enforces consistent series loads, distinct inter-series loads, and unique 1-based weighing indices.
- Evaluates span error: $\Delta E = \max(E) - \min(E) \le |MPE|$.

---

## Supporting / Applicability Capabilities

The Applicability Engine catalogs and evaluates applicability rules for additional R-76 clauses:
- **Tare Balancing & Tare Weighing** (Clause A.4.6)
- **Zero-Setting & Zero-Tracking** (Clause A.4.1, A.4.2, A.4.3)
- **Creep & Recovery** (Clause A.4.11)
- **Static Temperature** (Clause A.5.3)
- **Damp Heat, Steady State** (Clause A.5.4)
- **Voltage Variations** (Clause A.5.5)
- **Warm-Up Time** (Clause A.5.2)
- **Endurance Test** (Clause 3.9.4.3)

> **Important:** These supporting procedures are structured and evaluated at the applicability and test-planning level. *These procedures are not all deeply numerically implemented in the current prototype.*

---

## Metrological Safety & Integrity

The platform adheres to strict metrological software safety principles:
- **Arbitrary-Precision Decimal Arithmetic:** All calculations use Python's `Decimal` type to eliminate floating-point rounding errors.
- **Trusted Function Registries:** Calculation and compliance algorithms are dispatched through static, trusted in-memory registries (`CalculationEngine`, `ComplianceEngine`).
- **Zero Dynamic Code Execution:** Absolute ban on `eval()`, `exec()`, or runtime expression parsers.
- **Deterministic Decisions:** No artificial intelligence or LLMs are involved in PASS/FAIL/INCOMPLETE compliance determinations.
- **Fail-Closed Validation:** Missing or malformed configuration attributes halt execution immediately; string coercion (e.g., `"false"` $\to$ `True`) is strictly blocked.
- **No Fabricated Data:** The platform never substitutes default values (e.g., `0` or `10`) for missing measurement readings. Missing required inputs produce explicit `INCOMPLETE` results.
- **Observation Immutability:** Once a test attempt produces a calculation or compliance result, observations are locked against mutation (`ObservationLockedError`).
- **Audit-Preserved Retests:** Retests create Attempt $N+1$ linked via `supersedes_attempt_id`; failed historical attempts remain preserved in the audit trail.
- **Domain-Boundary Unit Normalization:** Laboratory observations preserve technician-entered values and units, while calculations normalize deterministically to authoritative configuration units (`kg`, `g`, `mg`).
- **End-to-End Traceability:** Complete bidirectional link from compliance decision back to raw observations, configuration snapshots, and physical instrument identifiers.

---

## Rule Versioning Architecture

Rules are decoupled from source code logic through versioned database records (`RuleVersion`):

```
RuleVersion
    ↓
calculation_identifier
    ↓
Trusted Calculation Registry (CalculationEngine)

RuleVersion
    ↓
criterion.type
    ↓
Trusted Compliance Registry (ComplianceEngine)
```

- Each evaluation captures a frozen `RuleVersion` ID and cryptographic `content_hash`.
- Evaluation plans bind to this snapshot, preventing retroactive standard shifts from mutating historical decisions.
- Missing or invalid rule version references fail closed without fallback to active defaults.

---

## Tech Stack

The backend is built with modern, type-safe Python components:
- **Language:** Python 3.11
- **API Framework:** FastAPI
- **Database:** PostgreSQL 16 (with relational integrity constraints)
- **ORM:** SQLAlchemy 2.0 (mapped column syntax)
- **Database Migrations:** Alembic
- **Validation & Schemas:** Pydantic v2
- **Precision Math:** Python standard library `Decimal`
- **Testing:** pytest (with PostgreSQL-backed test execution)

---

## System Architecture

### Data Model Hierarchy

```
Instrument
    ↓
InstrumentConfiguration (extra_capabilities JSON)
    ↓
Evaluation (frozen configuration_snapshot)
    ↓
EvaluationTest (range_index context)
    ↓
TestAttempt (attempt_number, supersedes_attempt_id)
    ↓
TestStep (procedural step guidance & metadata)
    ↓
Observation (raw laboratory readings & original units)
    ↓
Calculation (normalized inputs, formula outputs, execution audit)
    ↓
ComplianceResult (PASS / FAIL / INCOMPLETE)
    ↓
Evidence / AuditEvent (append-only ledger of state changes)
```

### Engine Responsibilities

- **Applicability Engine:** Analyzes instrument configuration snapshots against R-76 applicability criteria to generate the required evaluation plan.
- **Calculation Engine:** Pure mathematical function that takes normalized inputs and outputs calculated metrological figures ($P$, $E$, $E_c$, $\Delta E$).
- **Compliance Engine:** Evaluates calculated figures against applicable tolerance rules (e.g., Table 6 MPE steps) to produce an authoritative compliance decision.
- **MPE Engine:** Encapsulates Table 6 step limits across accuracy classes I, II, III, and IIII.

---

## Multi-Range Support

The platform provides first-class support for multiple-range instruments:
- Explicit `InstrumentConfigurationRange` entity storing range-specific `max_capacity`, `min_capacity`, `verification_scale_interval` ($e$), `actual_scale_interval` ($d$), and `unit`.
- Evaluation tests and attempts maintain explicit `range_index` context.
- Safe zero-indexing: `range_index is not None` checks ensure Range 0 (or Range 1) binds to range-specific parameters without falling back to global instrument metrics.

---

## Configuration-Driven Eccentricity

Eccentricity testing varies by platform design according to OIML R 76-1 Clause A.4.7. NAWI-OIML derives the procedure from `load_receptor` geometry metadata:

- **$\le 4$ Supports (Ordinary Platform):** Generates `FOUR_QUARTER_SEGMENTS` with positions `QUARTER_1`, `QUARTER_2`, `QUARTER_3`, `QUARTER_4`.
- **$> 4$ Supports (Multi-Support Platform):** Generates `SUPPORT_SPECIFIC` with positions `SUPPORT_1` through `SUPPORT_N`.
- **Special Receptor:** Generates `SPECIAL_RECEPTOR_SUPPORTS`.
- **Rolling Load:** Generates `ROLLING_LOAD` with positions `ROLL_BEGIN`, `ROLL_MIDDLE`, `ROLL_END`.

> **Scope Note:** This represents prototype-scoped procedure selection. Irregular or non-standard custom receptors fall back to `BLOCKED / UNSUPPORTED` rather than generating inaccurate test sequences.

---

## End-to-End Traceability Chain

Every compliance decision is forensically auditable back to original laboratory data:

```
PASS / FAIL / INCOMPLETE
   ↓
Compliance Criterion (e.g. ABS_LE_MPE)
   ↓
RuleVersion (OIML R 76-1: 2006 (E), content_hash)
   ↓
Calculation (formula outputs, execution timestamp)
   ↓
Normalized Calculation Inputs (load="15.000 kg", normalization_trace)
   ↓
Raw Observations (LOAD=15000 g, entered_by="tech_id", timestamp)
   ↓
Test Attempt (attempt_number=2, supersedes_attempt_id)
   ↓
Evaluation Test (test_code="WEIGHING_PERFORMANCE")
   ↓
Evaluation (evaluation_number, frozen configuration_snapshot)
   ↓
Instrument (serial_number, manufacturer)
```

---

## Retest & Observation Immutability

When an instrument fails a test or requires mechanical adjustment:
1. **Attempt 1** is preserved permanently as `SUPERSEDED` or `COMPLETED` with its failing calculation and compliance result. Observations on Attempt 1 are locked.
2. A retest is initiated via `create_retest_attempt()`.
3. **Attempt 2** is created with `attempt_number=2` and `supersedes_attempt_id` pointing to Attempt 1.
4. New observations and fresh calculations are recorded on Attempt 2.

This preserves the complete legal metrology history for certification scrutiny.

---

## Verification Status

The Phase 2 backend has undergone rigorous automated testing and metrological hardening:

- **Total Pytest Tests:** 103 passed, 0 failed, 2 warnings (100% pass rate).
- **Regression Suite:** 39 authoritative regression scenarios verified in `tests/test_final_p2_verification.py`.
- **Database Verification:** PostgreSQL 16 tested via live container connection; all Alembic migrations applied cleanly; `/health` endpoint verified (`database_connected: true`).

Key verification documents:
- Comprehensive Audit: [`backend/PHASE2_FINAL_VERIFICATION.md`](file:///Users/harshkhem/Desktop/sih%202026/backend/PHASE2_FINAL_VERIFICATION.md)
- Compact Reviewer Walkthrough: [`backend/PHASE2_FINAL_WALKTHROUGH.md`](file:///Users/harshkhem/Desktop/sih%202026/backend/PHASE2_FINAL_WALKTHROUGH.md)

---

## Current Status

### Phase 2 — COMPLETE
### Ready for Phase 3

- **Backend metrological core is currently frozen at the Phase 2 checkpoint.**
- **Frontend / Phase 3 integration has not yet been started in this checkpoint.**

---

## How to Run

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 14+ running locally or in Docker

### 2. Environment Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update `.env` with your PostgreSQL connection parameters:
```env
ENVIRONMENT=development
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sih26035_metrology
```

### 4. Apply Database Migrations
```bash
alembic upgrade head
```

### 5. Seed Synthetic Demo Data
Seed standard OIML R-76 rules and synthetic demo instruments:
```bash
PYTHONPATH=. python scripts/seed.py
```

### 6. Run the Test Suite
```bash
pytest -v
```

### 7. Start the FastAPI Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## Disclaimer

> **This repository contains a software prototype developed for SIH26035. It is not an OIML-certified product and does not constitute official legal metrology approval or certification.**
>
> **The current prototype does not implement every OIML R-76 procedure.**

---

## Repository Structure

```
.
├── backend/
│   ├── alembic/                      # Database migration scripts
│   │   ├── versions/
│   │   │   ├── 0001_phase1_initial.py
│   │   │   └── 0002_phase2_r76_engine.py
│   │   └── env.py
│   ├── app/
│   │   ├── api/                      # REST API endpoints (v1)
│   │   │   └── v1/
│   │   │       ├── attempts.py
│   │   │       ├── evaluations.py
│   │   │       ├── evidence.py
│   │   │       ├── instruments.py
│   │   │       ├── observations.py
│   │   │       └── tests.py
│   │   ├── core/                     # Application configuration & settings
│   │   ├── db/                       # SQLAlchemy engine & session setup
│   │   ├── engines/                  # Authoritative metrological engines
│   │   │   ├── applicability.py
│   │   │   ├── calculation.py
│   │   │   ├── compliance.py
│   │   │   └── mpe.py
│   │   ├── models/                   # SQLAlchemy declarative models
│   │   ├── schemas/                  # Pydantic v2 schemas
│   │   ├── services/                 # Business logic & workflow services
│   │   │   ├── calculation_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── test_service.py
│   │   │   └── trace_service.py
│   │   └── main.py                   # FastAPI application factory
│   ├── docs/                         # Reference standards documentation
│   ├── scripts/                      # Seed & demo execution scripts
│   │   ├── demo_killer_scenario.py
│   │   └── seed.py
│   ├── tests/                        # 103 PostgreSQL-backed pytest tests
│   │   ├── conftest.py
│   │   ├── test_applicability.py
│   │   ├── test_correctness_p0_p1.py
│   │   ├── test_correctness_p2_2.py
│   │   ├── test_final_p2_verification.py
│   │   ├── test_golden_r76.py
│   │   ├── test_health.py
│   │   ├── test_models.py
│   │   ├── test_mpe_engine.py
│   │   ├── test_retest_and_immutability.py
│   │   ├── test_services.py
│   │   └── test_validation.py
│   ├── .env.example                  # Template configuration without secrets
│   ├── .gitignore                    # Backend gitignore
│   ├── alembic.ini                   # Alembic configuration
│   ├── BACKEND_MASTER_SPEC.md        # Master architectural specification
│   ├── PHASE2_FINAL_VERIFICATION.md  # Comprehensive Phase 2 verification report
│   ├── PHASE2_FINAL_WALKTHROUGH.md   # Compact Phase 2 reviewer walkthrough
│   ├── pyproject.toml                # Project metadata & tool config
│   └── requirements.txt              # Production & development dependencies
├── .gitignore                        # Root secret-safety gitignore
└── README.md                         # Project documentation
```
