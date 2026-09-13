# SIH26035 — OIML R-76 Type Evaluation Backend (Phase 2)

This is the backend platform for automating **OIML R-76 Non-Automatic Weighing Instrument (NAWI) Type Evaluations**.

Phase 2 builds upon the Phase 1 foundation to implement the core USP:
**The Configuration-Driven R-76 Type-Evaluation Metrological Engine**.

```
Instrument Configuration
        ↓
Applicability Engine
        ↓
Applicable R-76 Test Plan
        ↓
Test Instance
        ↓
Observation Capture
        ↓
Calculation Engine
        ↓
Compliance Engine
        ↓
Traceable Result
```

---

## 1. Project Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/                  # Version 1 REST API routers
│   │       ├── instruments.py   # Instrument & configuration management
│   │       ├── evaluations.py   # Evaluation session & plan generation
│   │       ├── tests.py         # Evaluation test inspection & retesting
│   │       ├── attempts.py      # Execution attempts, observations, calculations, trace
│   │       ├── observations.py  # Observation modification with audit trails
│   │       └── evidence.py      # Evidence artifact metadata
│   ├── core/                    # Application settings & logging config
│   ├── db/                      # SQLAlchemy session, engine, and base
│   ├── engines/                 # Authoritative metrological engines
│   │   ├── applicability.py     # Deterministic R-76 rule evaluation
│   │   ├── calculation.py       # A.4.4.3, A.4.7, A.4.10 Decimal calculations
│   │   ├── compliance.py        # Deterministic PASS/FAIL/INCOMPLETE evaluator
│   │   └── mpe.py               # Table 6 Maximum Permissible Error engine
│   ├── models/                  # 16 SQLAlchemy 2.x declarative models
│   ├── schemas/                 # Pydantic v2 validation & response models
│   ├── services/                # Use-case services (plan, calculation, trace, test)
│   └── main.py                  # FastAPI application entrypoint
├── alembic/
│   └── versions/
│       ├── 0001_phase1_initial.py
│       └── 0002_phase2_r76_engine.py
├── scripts/
│   ├── seed.py                  # Safe synthetic database seed
│   └── demo_killer_scenario.py  # 15-step end-to-end killer demo execution
├── tests/                       # 37 comprehensive pytest tests
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 2. Setup and Installation

### 2.1 Prerequisites
* Python 3.10+ (Python 3.11 recommended)
* PostgreSQL 14+ (or Docker)

### 2.2 Create and Activate Virtual Environment
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment & PostgreSQL Configuration

### 3.1 Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure `.env` with your PostgreSQL credentials:
```env
ENVIRONMENT=development
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sih26035_metrology
```

*(Alternatively, specify `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/sih26035_metrology`)*.

### 3.2 Ensure PostgreSQL Database Exists
Using `psql`:
```sql
CREATE DATABASE sih26035_metrology;
```
Or via Docker:
```bash
docker run --name partnerhub-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=sih26035_metrology -p 5432:5432 -d postgres:16
```

---

## 4. Database Migrations (Alembic)

Run all migrations up to the latest revision (`0002_phase2_r76_engine`):
```bash
alembic upgrade head
```

To roll back:
```bash
alembic downgrade -1
```

---

## 5. Seeding Synthetic Demo Data

Seed standard canonical test definitions, rule versions with content hash, single-range NAWI, and multi-range NAWI:
```bash
python -m scripts.seed
```

> **Metrological Safety Guardrail:**
> All demo instruments (`SYNTH-DEMO-NAWI-001-SN`, `SYNTH-DEMO-MULTI-002-SN`) have `is_synthetic=True`. They are test-bench fixtures and must never be represented as real certified instruments.

---

## 6. Running FastAPI Server

Start the local development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Interactive API Documentation:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 7. Running Pytest Suite

Run all 37 unit, engine, and REST integration tests:
```bash
pytest -v
```

---

## 8. Phase 2 Metrological Architecture

### 8.1 Rule & Version Immutability
* Rules are represented as canonical structured JSON in `rule_versions.definition_json`.
* An immutable SHA-256 `content_hash` is computed from the canonical definition.
* Once linked to an evaluation, a `rule_version_id` is permanent.

### 8.2 Configuration Snapshot Immutability
* When an evaluation is created, a frozen JSON snapshot of the instrument configuration (including partial weighing ranges) is captured.
* All applicability evaluations, test plan generations, and MPE lookups use this frozen snapshot.
* Subsequent changes to the live instrument configuration do not mutate historical evaluations.

### 8.3 Applicability Engine (`app/engines/applicability.py`)
* Evaluates frozen snapshot to determine applicable tests.
* Supports OIML R 76-1:2006 requirements:
  - Weighing Performance (A.4.4): mandatory for all NAWIs.
  - Multi-Range Expansion: instruments with `is_multiple_range=True` expand into independent partial range tests (`WEIGHING_PERFORMANCE_RANGE_1`, `WEIGHING_PERFORMANCE_RANGE_2`).
  - Eccentricity (A.4.7): mandatory.
  - Repeatability (A.4.10): mandatory.
  - Tare (A.4.6): applicable when tare facility is configured (`tare_type != NONE`).
  - Endurance (3.9.4.3 & A.6): applicable **only** to Classes II, III, and IIII with $\text{Max} \le 100\text{ kg}$.
  - Warm-up & Voltage variation (A.5.2, A.5.4): applicable only to electronic instruments.

### 8.4 Authoritative MPE Engine (`app/engines/mpe.py`)
* Implements Table 6 (Clause 3.5.1) for Classes I, II, III, IIII.
* Expressed in verification scale intervals $m = L / e$:
  - Class III:
    - $0 \le m \le 500 \to 0.5e$
    - $500 < m \le 2000 \to 1.0e$
    - $2000 < m \le 10000 \to 1.5e$
* Uses Python `Decimal` exclusively; floating-point arithmetic is strictly forbidden.

### 8.5 Calculation Engine (`app/engines/calculation.py`)
* Registry-based dispatch architecture (`@CalculationEngine.register`).
* **A.4.4.3 Error Calculation**:
  $$P = I + 0.5e - \Delta L$$
  $$E = P - L$$
  $$E_c = E - E_0$$
* Stores complete input snapshot alongside calculation output.

### 8.6 Compliance Engine (`app/engines/compliance.py`)
* Strictly decoupled from calculation logic.
* Computes deterministic PASS/FAIL/INCOMPLETE decisions with tolerance margins and structured human explanations.
* Zero LLM/AI invocation.

### 8.7 Retest Lifecycle & Audit History
* When an instrument fails or is adjusted, a new `TestAttempt` (Attempt $N+1$) is created via `POST /api/v1/evaluation-tests/{id}/attempts`.
* Attempt 1 remains in the database with its raw observations, calculations, and `FAIL` compliance decision.
* Attempt 2 receives new observations and records its own calculations and `PASS` decision.
* Both attempts remain permanently available in the audit trail.

---

## 9. Phase 2 REST API Endpoints (`/api/v1`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health & PostgreSQL connectivity |
| `POST` | `/api/v1/instruments` | Register new weighing instrument |
| `GET` | `/api/v1/instruments` | List registered instruments |
| `GET` | `/api/v1/instruments/{id}` | Get instrument details |
| `POST` | `/api/v1/instruments/{id}/configurations` | Create metrological configuration |
| `GET` | `/api/v1/instruments/{id}/configurations/{cfg_id}` | Get configuration details |
| `POST` | `/api/v1/instruments/{id}/evaluations` | Initialize evaluation & capture frozen snapshot |
| `GET` | `/api/v1/evaluations/{id}` | Get evaluation details |
| `POST` | `/api/v1/evaluations/{id}/generate-plan` | Generate deterministic R-76 test plan |
| `GET` | `/api/v1/evaluations/{id}/plan` | Retrieve generated test plan |
| `GET` | `/api/v1/evaluations/{id}/tests` | List instantiated evaluation tests |
| `GET` | `/api/v1/evaluation-tests/{id}` | Get test details with attempts & steps |
| `POST` | `/api/v1/evaluation-tests/{id}/attempts` | Create new retest attempt (preserving history) |
| `GET` | `/api/v1/test-attempts/{id}` | Get attempt details |
| `POST` | `/api/v1/test-attempts/{id}/observations` | Record raw observation (L, I, ΔL, E0) |
| `GET` | `/api/v1/test-attempts/{id}/observations` | List raw observations |
| `PATCH`| `/api/v1/observations/{id}` | Modify observation with audit logging |
| `POST` | `/api/v1/test-attempts/{id}/calculate` | Execute calculation & compliance decision |
| `GET` | `/api/v1/test-attempts/{id}/calculations` | List calculations history |
| `GET` | `/api/v1/test-attempts/{id}/result` | Retrieve latest compliance result |
| `GET` | `/api/v1/test-attempts/{id}/trace` | Full audit traceability chain |
| `POST` | `/api/v1/test-attempts/{id}/evidence` | Attach evidence artifact metadata |
| `GET` | `/api/v1/evaluations/{id}/evidence` | List all evidence artifacts for evaluation |

---

## 10. Executing the 15-Step Killer Demo

To run the end-to-end killer demo proving all 15 steps against PostgreSQL:
```bash
python -m scripts.demo_killer_scenario
```
