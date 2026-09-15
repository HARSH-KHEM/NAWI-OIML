# METRA R-76 Evaluation Platform — Frontend Implementation Plan
**Problem Statement:** SIH26035 (NAWI Type-Evaluation Platform according to OIML R 76)  
**Baseline Git Commit:** `76ca3b4` (`feat: add METRA R-76 frontend visual foundation`)  
**Backend Status:** Validated Phase 2 (103 passed, 0 failed, 2 warnings)  
**Target Architecture:** Two-layer Next.js App Router + Top Navigation + Real API Client Layer

---

## 1. Executive Summary & Audit Findings

### 1.1 Current Repository State
- **Workspace Root:** `/Users/harshkhem/Desktop/sih 2026`
- **Backend:** FastAPI, SQLAlchemy 2.x, PostgreSQL, Alembic, Pytest. Exposes `/api/v1` with 17 endpoints across instruments, configurations, evaluations, test plans, attempts, observations, calculations, trace, and evidence.
- **Frontend App:** `/Users/harshkhem/Desktop/sih 2026/frontend/nawi-r-76-evaluation-platform`
  - Stack: Next.js 16.3.3 (Turbopack, App Router), React 19, TypeScript 5.7.3, Tailwind CSS v4 (`@tailwindcss/postcss` 4.3.3).
  - Current structure: Monolithic client component in `app/page.tsx` switching screens (`overview`, `config`, `plan`, `test`, `result`, `evidence`, `report`) via `useState`.
  - Styling: `app/globals.css` (28.8 KB) with custom engineering dark mode palette (`--black: #0b0d0c`, `--lime: #c8f36b`, `--warm: #f0efe9`, `--panel: #121614`).

### 1.2 Identified Frontend / Backend Mismatches & Technical Inaccuracies
1. **Fictitious Procedure Names in Current Mock:**
   - The mock defines `P-04: Range 2 transition` (A.4.4) and `P-05: Range 2 repeatability` (A.4.10).
   - *Authoritative R-76 Domain Reality:* In OIML R 76-1:2006 A.4.4.4, multi-range instruments instantiate partial weighing range tests: `WEIGHING_PERFORMANCE_RANGE_1` and `WEIGHING_PERFORMANCE_RANGE_2`.
   - The backend applicability engine dynamically derives up to 10 procedures: `WEIGHING_PERFORMANCE` (single or per-range), `ECCENTRICITY` (geometry-dependent), `REPEATABILITY` (dual-series), `TARE`, `ZERO_SETTING`, `CREEP`, `TEMPERATURE`, `VOLTAGE_VARIATION`, `WARM_UP`, `ENDURANCE`.
2. **Missing Input Fields for Authoritative Weighing Error Calculation:**
   - The current mock only has a single input: `Indication [ 100.021 ]`.
   - *Authoritative R-76 Equation:*
     $$P = I + \frac{1}{2}e - \Delta L$$
     $$E = P - L$$
     $$E_c = E - E_0$$
     Requires turning-point additional weights $\Delta L$ (`ADDITIONAL_LOAD`) and zero error $E_0$ (`ZERO_ERROR`) to determine compliance against Table 6 MPE limits.
3. **Missing Eccentricity Load Receptor Geometry:**
   - Real backend requires `load_receptor` metadata (`support_count`, `special_receptor`, `rolling_load`) to determine the exact A.4.7 eccentricity procedure (`FOUR_QUARTER_SEGMENTS` vs. `SUPPORT_SPECIFIC` vs. `ROLLING_LOAD`). Without it, backend fails closed as `BLOCKED`.
4. **Missing Backend List & Reporting Endpoints:**
   - `GET /api/v1/evaluations` (list evaluations with filter/search) is missing.
   - `GET /api/v1/rule-versions` (list rule versions) is missing.
   - `GET /api/v1/instruments/{id}/configurations` (list configurations for an instrument) is missing.
   - `GET /api/v1/evaluations/{id}/report` (consolidated report payload) is missing.

---

## 2. Target Information Architecture & Navigation

### 2.1 Two-Layer UX Structure
- **Layer A — Overview Landing Page (`/`):**
  Full-width, scroll-driven interactive product showcase. Explains the core differentiator:
  $$\text{Instrument Configuration} \longrightarrow \text{Applicability Engine} \longrightarrow \text{Executable Test Plan} \longrightarrow \text{Calculations} \longrightarrow \text{Traceable Evidence}$$
  Includes interactive micro-demonstrations (e.g. toggling Multiple Range on/off to preview dynamic plan expansion), key metrics, and direct CTAs to application workflows.
- **Layer B — Dedicated Application Pages:**
  Deep, dense, workstation-grade metrological evaluation screens.
  - `/evaluations` — Evaluation repository, filterable by status, class, instrument.
  - `/evaluations/new` — Guided wizard: Select/Register Instrument $\rightarrow$ Configure Specifications $\rightarrow$ Choose Rule Version $\rightarrow$ Initialize Evaluation.
  - `/evaluations/[id]` — Evaluation hub with pipeline stepper (`01 Configure` $\rightarrow$ `02 Applicability` $\rightarrow$ `03 Test Plan` $\rightarrow$ `04 Guided Test` $\rightarrow$ `05 Calculate` $\rightarrow$ `06 Evidence` $\rightarrow$ `07 Report`).
  - `/evaluations/[id]/plan` — Live test plan derived from frozen configuration snapshot with "Why is this applicable?" clause inspectability.
  - `/evaluations/[id]/tests/[testId]` — Guided laboratory operator test workspace with exact observation inputs, turning-point calculation, and real-time MPE tolerance verification.
  - `/evaluations/[id]/evidence` — Traceability chain graph ($Decision \rightarrow Criterion \rightarrow RuleVersion \rightarrow Calculation \rightarrow Observation \rightarrow Test \rightarrow Snapshot$).
  - `/evaluations/[id]/report` — Standardized OIML R-76 technical report preview and export.
  - `/instruments` — Registered instrument catalogue (synthetic demo fixtures + real instruments).
  - `/test-plans` — Master catalogue of OIML R-76 test definitions.
  - `/reports` — Generated technical evaluation reports index.

### 2.2 Navigation Architecture
Top navigation header across all pages:
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ [⚡ METRA  R-76/EVALUATION ENGINE]    Overview   Evaluations   Instruments   Test Plans   Reports │
│                                                                [Search ⌘K]  [Rule: R-76:2006] [AM] │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture & Directory Structure

```
frontend/nawi-r-76-evaluation-platform/
├── app/
│   ├── layout.tsx                    # Root layout with TopNav and metadata
│   ├── page.tsx                      # Layer A: Full-width scrolling Overview
│   ├── evaluations/
│   │   ├── page.tsx                  # Evaluations list & status dashboard
│   │   ├── new/
│   │   │   └── page.tsx              # Create new evaluation wizard
│   │   └── [id]/
│   │       ├── layout.tsx            # Evaluation shell with Pipeline stepper & subnav
│   │       ├── page.tsx              # Evaluation Overview / Summary
│   │       ├── configuration/page.tsx# Frozen snapshot & capability inspect
│   │       ├── plan/page.tsx         # Applicability & dynamic test plan
│   │       ├── tests/[testId]/page.tsx# Guided laboratory execution workspace
│   │       ├── compliance/page.tsx   # Deterministic calculation & MPE compliance
│   │       ├── evidence/page.tsx     # Traceability graph
│   │       └── report/page.tsx       # Standardized technical report preview
│   ├── instruments/
│   │   ├── page.tsx                  # Instrument catalogue
│   │   └── [id]/page.tsx             # Instrument specifications & configuration history
│   ├── test-plans/
│   │   └── page.tsx                  # Canonical R-76 test procedures catalog
│   └── reports/
│       └── page.tsx                  # Master reports directory
├── components/
│   ├── layout/
│   │   ├── top-nav.tsx               # Top navigation bar
│   │   ├── evaluation-pipeline.tsx   # 01-07 Pipeline progression stepper
│   │   └── breadcrumbs.tsx           # Contextual breadcrumb trail
│   ├── overview/
│   │   ├── hero-section.tsx          # Editorial hero with value proposition
│   │   ├── applicability-demo.tsx    # Interactive single vs. multi-range toggle demo
│   │   ├── test-plan-preview.tsx     # Rule-derived sequence preview
│   │   ├── calculation-preview.tsx   # Transparent formula breakdown card
│   │   ├── evidence-chain-preview.tsx# Sequential trace reveal
│   │   └── cta-section.tsx           # Launch evaluation CTA
│   ├── evaluations/
│   │   ├── procedure-card.tsx        # Card showing test code, clause, and status
│   │   ├── applicability-badge.tsx   # Status / inclusion indicator
│   │   ├── why-applicable-modal.tsx  # Reasoning drawer for R-76 clause justification
│   │   ├── observation-form.tsx      # Strict measurement input grid with unit normalization
│   │   ├── calculation-breakdown.tsx # Formula expansion (P, E, Ec, MPE)
│   │   ├── retest-dialog.tsx         # Safe Attempt N+1 creation without mutating history
│   │   └── evidence-graph.tsx        # Interactive compliance trace nodes
│   └── ui/
│       ├── badge.tsx
│       ├── button.tsx
│       ├── search-dialog.tsx
│       └── data-table.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts                 # Base HTTP client with error handling & base URL
│   │   ├── instruments.ts            # Instrument & configuration API endpoints
│   │   ├── evaluations.ts            # Evaluation lifecycle & test plan endpoints
│   │   ├── tests.ts                  # Test execution, attempts & retest endpoints
│   │   ├── observations.ts           # Observation submission & patch endpoints
│   │   ├── calculations.ts           # Calculation trigger & result endpoints
│   │   ├── evidence.ts               # Evidence trace & artifact endpoints
│   │   └── reports.ts                # Report generation endpoints
│   ├── types/
│   │   ├── domain.ts                 # Strict TypeScript mirrors of SQLAlchemy models & schemas
│   │   └── r76.ts                    # OIML R 76 constants (Accuracy classes, MPE limits, units)
│   ├── mock-data.ts                  # Realistic synthetic fallback fixtures (SYNTH-DEMO-NAWI-001)
│   └── utils.ts                      # Formatting & class merge helpers
```

---

## 4. Phased Implementation Roadmap

### Phase 1: Navigation, Overview Architecture & Evaluation Route Skeleton
- [ ] Create `components/layout/top-nav.tsx` implementing top-bar navigation (METRA, Overview, Evaluations, Instruments, Test Plans, Reports, Search, Rule Version indicator).
- [ ] Refactor `app/layout.tsx` to host top navigation globally.
- [ ] Deconstruct `app/page.tsx` into clean modular sections:
  - Hero section with editorial typography
  - Interactive Applicability Demonstration (Single vs Multi-Range toggle)
  - Applicable Test Plan preview
  - Deterministic Calculation showcase
  - Traceability Chain preview
  - Report handoff CTA
- [ ] Create route skeletons for:
  - `/evaluations`
  - `/evaluations/new`
  - `/evaluations/[id]`
  - `/evaluations/[id]/plan`
  - `/evaluations/[id]/tests/[testId]`
  - `/evaluations/[id]/evidence`
  - `/evaluations/[id]/report`
  - `/instruments`
  - `/test-plans`
  - `/reports`
- [ ] Verify build and type checking (`npm run build`, `tsc --noEmit`).
- [ ] Commit milestone checkpoint to Git.

### Phase 2: Instrument Catalog, Creation & Configuration Management
- [ ] Implement TypeScript domain types in `lib/types/domain.ts` reflecting backend Pydantic schemas (`InstrumentRead`, `InstrumentConfigurationRead`, etc.).
- [ ] Implement `lib/api/instruments.ts` connecting to `GET /api/v1/instruments`, `POST /api/v1/instruments`, `POST /api/v1/instruments/{id}/configurations`.
- [ ] Implement `/instruments` catalog page listing instruments (highlighting synthetic demo fixtures like `SYNTH-DEMO-NAWI-001`).
- [ ] Implement `/evaluations/new` configuration wizard with strict validation (Max, Min, e, d, accuracy class, single vs multiple range, load receptor geometry).

### Phase 3: Backend-Connected Evaluation Creation & Snapshot Freezing
- [ ] Implement `lib/api/evaluations.ts` for `POST /api/v1/instruments/{id}/evaluations` and `GET /api/v1/evaluations/{id}`.
- [ ] Implement `/evaluations/[id]` overview page displaying frozen configuration snapshot and audit metadata.
- [ ] Add missing backend endpoint `GET /api/v1/evaluations` with pytest test coverage.

### Phase 4: Dynamic Applicability Engine UI & Test Plan
- [ ] Connect `POST /api/v1/evaluations/{id}/generate-plan` and `GET /api/v1/evaluations/{id}/plan`.
- [ ] Build `/evaluations/[id]/plan` with dynamic procedure list, status badges (`IMPLEMENTED`, `APPLICABILITY_ONLY`, `PARTIAL`), and "Why Applicable?" drawer.
- [ ] Visually differentiate single-range plan (8-10 tests) vs multi-range plan (10-12 tests with range-specific weighing tests).

### Phase 5: Guided Laboratory Test Workflow & Observation Capture
- [ ] Build `/evaluations/[id]/tests/[testId]` laboratory execution workspace.
- [ ] Implement observation entry forms for:
  - Weighing Performance: `LOAD`, `INDICATION`, `ADDITIONAL_LOAD` ($\Delta L$), `ZERO_ERROR` ($E_0$).
  - Eccentricity: Position selection (`QUARTER_1` to `QUARTER_4` or `SUPPORT_1` to `SUPPORT_N`), test load, indication, zero error.
  - Repeatability: Series A (50% Max) and Series B (100% Max) loadings.
- [ ] Connect `POST /api/v1/test-attempts/{id}/observations`.
- [ ] Connect `POST /api/v1/evaluation-tests/{id}/attempts` for non-destructive retesting (Attempt N+1).

### Phase 6: Deterministic Calculation & Compliance Display
- [ ] Connect `POST /api/v1/test-attempts/{id}/calculate` and `GET /api/v1/test-attempts/{id}/result`.
- [ ] Render step-by-step calculation path:
  - $P = I + 0.5e - \Delta L$
  - $E = P - L$
  - $E_c = E - E_0$
  - Limit comparison: $|E_c| \le \text{MPE}$
- [ ] Display deterministic badge: "Rule Version R-76-1:2006 · No AI in decision".

### Phase 7: Evidence Traceability Chain
- [ ] Connect `GET /api/v1/test-attempts/{id}/trace` and `GET /api/v1/evaluations/{id}/evidence`.
- [ ] Render interactive traceability graph:
  $$\text{PASS} \rightarrow \text{Criterion (MPE)} \rightarrow \text{Rule Clause} \rightarrow \text{Calculation} \rightarrow \text{Observation} \rightarrow \text{Test} \rightarrow \text{Configuration Snapshot} \rightarrow \text{Rule Version}$$

### Phase 8: Standardized Technical Report Generation
- [ ] Add backend endpoint `GET /api/v1/evaluations/{id}/report` returning full evaluation summary.
- [ ] Build `/evaluations/[id]/report` rendering official OIML R-76 format (Equipment specification, test results summary, compliance table, evidence list, signature block).
- [ ] Support print/PDF export styling.

---

## 5. Verification & Quality Gates
- **Frontend Quality Gate:** Every milestone must pass `npm run build` and `npx tsc --noEmit` with zero errors.
- **Backend Quality Gate:** Every milestone touching backend must pass `pytest` (maintaining 103 passed, 0 failed, 2 warnings or higher).
- **Git Discipline:** Small, focused, descriptive commits following conventional commit syntax.
