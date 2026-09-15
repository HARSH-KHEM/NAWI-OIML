'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronRight,
  Play,
  RotateCcw,
  ShieldCheck,
  TestTube2,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function GuidedTestWorkspacePage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const testId = (params?.testId as string) || 'test-wp-01'

  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]
  const inst = evaluation.instrument

  // Guided test observation state (A.4.4.3 Weighing Performance test point at L = 10 kg)
  const [load, setLoad] = useState('10.000')
  const [indication, setIndication] = useState('10.000')
  const [additionalLoad, setAdditionalLoad] = useState('0.003') // ΔL turning point weights
  const [zeroError, setZeroError] = useState('0.000') // E0
  const [calculated, setCalculated] = useState(false)
  const [attemptNumber, setAttemptNumber] = useState(1)

  // Real-time calculation preview
  const numI = parseFloat(indication) || 0
  const numE = parseFloat(String(inst.verificationScaleInterval)) || 0.01
  const numDeltaL = parseFloat(additionalLoad) || 0
  const numL = parseFloat(load) || 10
  const numE0 = parseFloat(zeroError) || 0

  // P = I + 0.5e - ΔL
  const calculatedP = numI + 0.5 * numE - numDeltaL
  // E = P - L
  const calculatedE = calculatedP - numL
  // Ec = E - E0
  const calculatedEc = calculatedE - numE0
  // MPE for 10 kg (1000 e) under Class III is ±1.0 e = ±0.010 kg
  const mpe = 0.01
  const isPass = Math.abs(calculatedEc) <= mpe

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={3} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>04</span>Guided Laboratory Execution Workspace
          </div>
          <h1>Weighing Performance Test</h1>
          <p>
            OIML R 76-1:2006 · Clause A.4.4 · Evaluation Test Point 01 (Ascending Load: 10.000 kg)
          </p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="button button-secondary"
            onClick={() => setAttemptNumber((prev) => prev + 1)}
            title="Create Attempt N+1 without overwriting Attempt 1 history"
          >
            <RotateCcw style={{ width: '13px' }} /> Record retest (Attempt #{attemptNumber + 1})
          </button>
          <Link href={`/evaluations/${evaluation.id}/compliance`} className="button">
            View compliance path <ArrowRight />
          </Link>
        </div>
      </div>

      <div className="test-layout">
        {/* Left: Test Procedure Stepper Rail */}
        <aside className="panel test-rail">
          <span className="eyebrow">Active Attempt</span>
          <strong style={{ margin: '10px 0 16px', display: 'block' }}>
            Attempt #{attemptNumber} <Badge tone="lime">In Progress</Badge>
          </strong>

          <div className="rail-progress" aria-hidden="true">
            <i style={{ width: '40%' }} />
          </div>

          <div className="rail-procedure current">
            <span>
              <Play style={{ width: '10px' }} />
            </span>
            <span>Point 1: 10.000 kg (Ascending)</span>
          </div>
          <div className="rail-procedure">
            <span>02</span>
            <span>Point 2: 20.000 kg (Ascending)</span>
          </div>
          <div className="rail-procedure">
            <span>03</span>
            <span>Point 3: 30.000 kg (Max Capacity)</span>
          </div>
          <div className="rail-procedure">
            <span>04</span>
            <span>Point 4: 20.000 kg (Descending)</span>
          </div>
          <div className="rail-procedure">
            <span>05</span>
            <span>Point 5: 10.000 kg (Descending)</span>
          </div>
        </aside>

        {/* Right: Operator Input Workspace Panel */}
        <div className="panel test-panel">
          <div className="test-meta">
            <Badge tone="outline">WP-POINT-01</Badge>
            <span>OIML R 76-1:2006 · A.4.4.3 Intrinsic Error</span>
            <span className="test-meta-right">DECIMAL PRECISION ARITHMETIC</span>
          </div>

          <div className="test-title" style={{ margin: '24px 0 20px' }}>
            <span className="eyebrow lime-text">Laboratory Instruction</span>
            <h2 style={{ fontSize: '26px', margin: '8px 0 6px' }}>
              Apply 10.000 kg test weights centrally on the load receptor.
            </h2>
            <p>
              Observe the displayed indication. Add successive small weights (ΔL) until the indication
              unambiguously switches to the next scale interval (I + e) to determine rounding error.
            </p>
          </div>

          {/* Observation Inputs Grid */}
          <div className="observation-grid">
            <div className="observation-field">
              <label>
                Applied Test Load (L) <span>kg</span>
              </label>
              <input
                type="text"
                value={load}
                onChange={(e) => setLoad(e.target.value)}
                aria-label="Applied test load"
              />
              <small>Calibrated standard test mass</small>
            </div>

            <div className="observation-field active-field">
              <label>
                Observed Indication (I) <span>kg</span>
              </label>
              <input
                type="text"
                value={indication}
                onChange={(e) => setIndication(e.target.value)}
                aria-label="Observed indication"
              />
              <small>Instrument displayed indication</small>
            </div>

            <div className="observation-field">
              <label>
                Turning Weights (ΔL) <span>kg</span>
              </label>
              <input
                type="text"
                value={additionalLoad}
                onChange={(e) => setAdditionalLoad(e.target.value)}
                aria-label="Additional turning point load"
              />
              <small>Clause A.4.4.3 additional load</small>
            </div>

            <div className="observation-field">
              <label>
                Zero-Load Error (E0) <span>kg</span>
              </label>
              <input
                type="text"
                value={zeroError}
                onChange={(e) => setZeroError(e.target.value)}
                aria-label="Zero error"
              />
              <small>Calculated error at zero load</small>
            </div>

            <div className="observation-field">
              <label>
                Scale Interval (e) <span>kg</span>
              </label>
              <strong>{inst.verificationScaleInterval}</strong>
              <small>From frozen snapshot</small>
            </div>

            <div className="observation-field">
              <label>
                Table 6 MPE Tier <span>kg</span>
              </label>
              <strong>±{mpe.toFixed(3)}</strong>
              <small>±1.0 e for 500e &lt; m ≤ 2000e</small>
            </div>
          </div>

          {/* Validation & Computed Live Result */}
          <div className="validation-note" style={{ marginTop: '20px' }}>
            <Check aria-hidden="true" />
            <div>
              <strong>Deterministic calculation evaluated:</strong>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '11px', display: 'block', marginTop: '4px' }}>
                P = {calculatedP.toFixed(3)} kg · Error E = {calculatedE >= 0 ? `+${calculatedE.toFixed(3)}` : calculatedE.toFixed(3)} kg · Corrected Ec = {calculatedEc >= 0 ? `+${calculatedEc.toFixed(3)}` : calculatedEc.toFixed(3)} kg
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '28px', flexWrap: 'wrap', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Badge tone={isPass ? 'lime' : 'red'}>
                {isPass ? 'PASS · WITHIN MPE' : 'FAIL · EXCEEDS MPE'}
              </Badge>
              <span style={{ color: 'var(--dim)', font: '10px ui-monospace, monospace' }}>
                |{calculatedEc.toFixed(3)}| ≤ {mpe.toFixed(3)} kg
              </span>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <Link href={`/evaluations/${evaluation.id}/plan`} className="button button-secondary">
                Back to test plan
              </Link>
              <Link href={`/evaluations/${evaluation.id}/compliance`} className="button">
                Commit & view compliance <ArrowRight />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
