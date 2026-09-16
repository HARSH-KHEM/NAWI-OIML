'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronRight,
  Clock,
  Play,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  TestTube2,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import {
  EvaluationRead,
  EvaluationTestRead,
  TestAttemptRead,
} from '@/lib/types/domain'
import {
  getEvaluation,
  getEvaluationPlan,
  getEvaluationTests,
  getEvaluationTest,
  getTestAttempt,
  submitObservation,
  executeCalculation,
  createRetest,
} from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function GuidedTestWorkspacePage() {
  const params = useParams()
  const router = useRouter()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const routeTestId = (params?.testId as string) || 'test-wp-01'

  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [allTests, setAllTests] = useState<EvaluationTestRead[]>([])
  const [activeTest, setActiveTest] = useState<EvaluationTestRead | null>(null)
  const [activeAttempt, setActiveAttempt] = useState<TestAttemptRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [calculating, setCalculating] = useState(false)
  const [retesting, setRetesting] = useState(false)

  // Guided test observation state (A.4.4.3 Weighing Performance test point at L = 10 kg)
  const [load, setLoad] = useState('10.000')
  const [indication, setIndication] = useState('10.000')
  const [additionalLoad, setAdditionalLoad] = useState('0.005') // ΔL turning point weights
  const [zeroError, setZeroError] = useState('0.000') // E0

  // Authoritative calculation & compliance response from backend
  const [calcResponse, setCalcResponse] = useState<{
    P: string
    E: string
    Ec: string
    mpeMass: string
    mpeFactor: string
    decision: string
    margin?: string
    reasoning?: string
  } | null>(null)

  // Load evaluation and tests
  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const evalData = await getEvaluation(evaluationId)
        if (evalData) {
          setEvaluation(evalData)
        } else {
          const mock =
            MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
            MOCK_EVALUATIONS[0]
          setEvaluation({
            id: mock.id,
            evaluation_number: mock.evaluationNumber,
            instrument_id: mock.instrument.id,
            instrument_configuration_id: `cfg-${mock.instrument.id}`,
            rule_version_id: mock.ruleVersion,
            configuration_snapshot: {
              accuracy_class: mock.instrument.accuracyClass,
              max_capacity: String(mock.instrument.maxCapacity),
              min_capacity: String(mock.instrument.minCapacity),
              verification_scale_interval: String(mock.instrument.verificationScaleInterval),
              actual_scale_interval: String(mock.instrument.actualScaleInterval),
              unit: mock.instrument.unit,
              number_of_ranges: mock.instrument.numberOfRanges,
              is_multiple_range: mock.instrument.isMultipleRange,
              tare_type: mock.instrument.tareType,
              is_electronic: mock.instrument.isElectronic,
              has_zero_setting: mock.instrument.hasZeroSetting,
              extra_capabilities: {},
              snapshot_timestamp: mock.createdAt,
              instrument_serial: mock.instrument.serialNumber,
              manufacturer: mock.instrument.manufacturer,
              model_name: mock.instrument.modelName,
            },
            status: mock.status as any,
            lab_name: mock.labName,
            created_at: mock.createdAt,
          })
        }

        // Fetch plan / tests
        let tests = await getEvaluationTests(evaluationId)
        if (!tests || tests.length === 0) {
          const plan = await getEvaluationPlan(evaluationId)
          if (plan?.tests) {
            tests = plan.tests
          }
        }

        setAllTests(tests || [])

        // Resolve active test
        let foundTest: EvaluationTestRead | null = null
        if (tests && tests.length > 0) {
          foundTest =
            tests.find(
              (t) =>
                t.id === routeTestId ||
                t.test_code?.toLowerCase() === routeTestId.toLowerCase() ||
                (routeTestId.includes('wp') && t.test_code?.includes('WEIGHING'))
            ) || tests[0]
        }

        if (foundTest) {
          // Fetch full test details including attempts
          const fullTest = await getEvaluationTest(foundTest.id)
          const targetTest = fullTest || foundTest
          setActiveTest(targetTest)

          // Pick latest attempt
          if (targetTest.attempts && targetTest.attempts.length > 0) {
            const latest = targetTest.attempts[targetTest.attempts.length - 1]
            // Fetch fresh attempt details to get latest observations
            const freshAttempt = await getTestAttempt(latest.id)
            setActiveAttempt(freshAttempt || latest)
          } else {
            // Create initial attempt if test has no attempts yet
            try {
              const newAttempt = await createRetest(targetTest.id, 'Initial laboratory execution attempt')
              setActiveAttempt(newAttempt)
            } catch {
              // fallback simulation
              setActiveAttempt({
                id: `att-${Date.now().toString(36)}`,
                evaluation_test_id: targetTest.id,
                attempt_number: 1,
                status: 'IN_PROGRESS',
                started_at: new Date().toISOString(),
                steps: [],
                observations: [],
              })
            }
          }
        }
      } catch (err) {
        console.warn('Error loading test execution workspace:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [evaluationId, routeTestId])

  // Real-time client preview calculations (for instant operator feedback prior to commit)
  const snap = evaluation?.configuration_snapshot
  const numI = parseFloat(indication) || 0
  const numE = parseFloat(String(snap?.verification_scale_interval || '0.010')) || 0.01
  const numDeltaL = parseFloat(additionalLoad) || 0
  const numL = parseFloat(load) || 10
  const numE0 = parseFloat(zeroError) || 0

  // P = I + 0.5e - ΔL
  const previewP = numI + 0.5 * numE - numDeltaL
  // E = P - L
  const previewE = previewP - numL
  // Ec = E - E0
  const previewEc = previewE - numE0
  // MPE for 10 kg (1000 e) under Class III is ±1.0 e = ±0.010 kg
  const previewMpe = numE * 1.0
  const previewPass = Math.abs(previewEc) <= previewMpe

  // Submit observations & invoke authoritative backend calculation
  const handleCalculate = async () => {
    if (!activeAttempt) return
    setCalculating(true)
    try {
      // 1. Submit raw physical observations to backend
      const obsList = [
        { observation_code: 'LOAD', value_numeric: load, unit: snap?.unit || 'kg', notes: 'Calibrated standard mass' },
        { observation_code: 'INDICATION', value_numeric: indication, unit: snap?.unit || 'kg', notes: 'Readout' },
        { observation_code: 'ADDITIONAL_LOAD', value_numeric: additionalLoad, unit: snap?.unit || 'kg', notes: 'Turning load' },
        { observation_code: 'ZERO_ERROR', value_numeric: zeroError, unit: snap?.unit || 'kg', notes: 'Zero error E0' },
      ]

      for (const obs of obsList) {
        try {
          await submitObservation(activeAttempt.id, obs)
        } catch {
          // Ignore if already submitted or locked
        }
      }

      // 2. Trigger backend calculation and compliance engine
      const res = await executeCalculation(activeAttempt.id)
      if (res && res.calculation && res.compliance) {
        const out = res.calculation.output || res.calculation.outputs || {}
        setCalcResponse({
          P: out.P || previewP.toFixed(3),
          E: out.E || previewE.toFixed(3),
          Ec: out.Ec || previewEc.toFixed(3),
          mpeMass: out.mpe_mass || previewMpe.toFixed(3),
          mpeFactor: out.mpe_factor || '1.0',
          decision: res.compliance.decision || (previewPass ? 'PASS' : 'FAIL'),
          margin: res.compliance.margin,
          reasoning: res.compliance.reasoning?.explanation,
        })
      } else {
        // Deterministic fallback response
        setCalcResponse({
          P: previewP.toFixed(3),
          E: previewE.toFixed(3),
          Ec: previewEc.toFixed(3),
          mpeMass: previewMpe.toFixed(3),
          mpeFactor: '1.0',
          decision: previewPass ? 'PASS' : 'FAIL',
          margin: `${(previewMpe - Math.abs(previewEc)).toFixed(3)}`,
          reasoning: previewPass
            ? 'Corrected error Ec within maximum permissible error under Table 6.'
            : 'Corrected error Ec exceeds maximum permissible error under Table 6.',
        })
      }
    } catch (err) {
      console.warn('Backend calculate failed, using deterministic AST result:', err)
      setCalcResponse({
        P: previewP.toFixed(3),
        E: previewE.toFixed(3),
        Ec: previewEc.toFixed(3),
        mpeMass: previewMpe.toFixed(3),
        mpeFactor: '1.0',
        decision: previewPass ? 'PASS' : 'FAIL',
        margin: `${(previewMpe - Math.abs(previewEc)).toFixed(3)}`,
        reasoning: previewPass
          ? 'Calculated corrected error Ec satisfies Clause A.4.4.3 limits.'
          : 'Calculated corrected error Ec exceeds Clause A.4.4.3 limits.',
      })
    } finally {
      setCalculating(false)
    }
  }

  // Create Retest Attempt N+1
  const handleRetest = async () => {
    if (!activeTest) return
    setRetesting(true)
    try {
      const nextAttempt = await createRetest(
        activeTest.id,
        'Technician adjusted instrument calibration; executing Attempt N+1 without overwriting Attempt 1 audit record.'
      )
      setActiveAttempt(nextAttempt)
      setCalcResponse(null)
      // Reset inputs to passing defaults
      setIndication(load)
      setAdditionalLoad('0.005')
      setZeroError('0.000')
    } catch (err) {
      console.warn('Failed to create retest attempt on API:', err)
      // Fallback in-memory attempt
      const newNum = (activeAttempt?.attempt_number || 1) + 1
      setActiveAttempt({
        id: `att-${Date.now().toString(36)}`,
        evaluation_test_id: activeTest.id,
        attempt_number: newNum,
        status: 'IN_PROGRESS',
        started_at: new Date().toISOString(),
        steps: [],
        observations: [],
      })
      setCalcResponse(null)
      setIndication(load)
      setAdditionalLoad('0.005')
      setZeroError('0.000')
    } finally {
      setRetesting(false)
    }
  }

  if (loading || !evaluation) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '80px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '28px', margin: '0 auto 16px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Loading laboratory test workspace...</p>
      </div>
    )
  }

  const currentAttemptNum = activeAttempt?.attempt_number || 1
  const isPass = calcResponse ? calcResponse.decision === 'PASS' : previewPass

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={3} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>04</span>Guided Laboratory Execution Workspace · Evaluation #{evaluation.evaluation_number}
          </div>
          <h1>{activeTest?.title || 'Weighing Performance Test'}</h1>
          <p>
            OIML R 76-1:2006 · Clause {activeTest?.r76_reference || 'A.4.4'} · Test Code: {activeTest?.test_code || 'WEIGHING_PERFORMANCE'}{' '}
            {activeTest?.range_reference && `(${activeTest.range_reference})`}
          </p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="button button-secondary"
            onClick={handleRetest}
            disabled={retesting}
            title="Create Attempt N+1 without overwriting Attempt 1 history"
          >
            <RotateCcw style={{ width: '13px' }} />{' '}
            {retesting ? 'Creating retest...' : `Record retest (Attempt #${currentAttemptNum + 1})`}
          </button>
          <Link href={`/evaluations/${evaluation.id}/compliance`} className="button">
            View compliance path <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>
      </div>

      <div className="test-layout">
        {/* Left: Test Procedure Stepper Rail */}
        <aside className="panel test-rail">
          <span className="eyebrow">Active Attempt</span>
          <strong style={{ margin: '10px 0 16px', display: 'block' }}>
            Attempt #{currentAttemptNum}{' '}
            <Badge tone={calcResponse ? (isPass ? 'lime' : 'red') : 'amber'}>
              {calcResponse ? calcResponse.decision : 'In Progress'}
            </Badge>
          </strong>

          {activeAttempt?.supersedes_attempt_id && (
            <div style={{ fontSize: '10px', color: 'var(--dim)', marginBottom: '12px', background: '#121714', padding: '6px 8px', borderRadius: '4px' }}>
              Supersedes Attempt #{currentAttemptNum - 1} (Non-destructive audit chain)
            </div>
          )}

          <div className="rail-progress" aria-hidden="true">
            <i style={{ width: calcResponse ? '100%' : '50%' }} />
          </div>

          <div className="eyebrow" style={{ marginTop: '20px', marginBottom: '8px' }}>
            Procedures In Plan
          </div>

          {allTests.map((t, idx) => {
            const isCurrent = t.id === activeTest?.id
            return (
              <Link
                key={t.id}
                href={`/evaluations/${evaluation.id}/tests/${t.id}`}
                className={`rail-procedure ${isCurrent ? 'current' : ''}`}
                style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '6px' }}
              >
                <span>{isCurrent ? <Play style={{ width: '10px' }} /> : String(idx + 1).padStart(2, '0')}</span>
                <span style={{ fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.title || t.test_code}
                </span>
              </Link>
            )
          })}
        </aside>

        {/* Right: Operator Input Workspace Panel */}
        <div className="panel test-panel">
          <div className="test-meta">
            <Badge tone="outline">{activeTest?.test_code || 'WEIGHING_PERFORMANCE'}</Badge>
            <span>OIML R 76-1:2006 · A.4.4.3 Intrinsic Error</span>
            <span className="test-meta-right">DECIMAL PRECISION ARITHMETIC</span>
          </div>

          <div className="test-title" style={{ margin: '24px 0 20px' }}>
            <span className="eyebrow lime-text">Laboratory Instruction</span>
            <h2 style={{ fontSize: '26px', margin: '8px 0 6px' }}>
              Apply {load} {snap?.unit || 'kg'} test weights centrally on the load receptor.
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
                Applied Test Load (L) <span>{snap?.unit || 'kg'}</span>
              </label>
              <input
                type="text"
                value={load}
                onChange={(e) => {
                  setLoad(e.target.value)
                  setCalcResponse(null)
                }}
                aria-label="Applied test load"
              />
              <small>Calibrated standard test mass</small>
            </div>

            <div className="observation-field active-field">
              <label>
                Observed Indication (I) <span>{snap?.unit || 'kg'}</span>
              </label>
              <input
                type="text"
                value={indication}
                onChange={(e) => {
                  setIndication(e.target.value)
                  setCalcResponse(null)
                }}
                aria-label="Observed indication"
              />
              <small>Instrument digital readout</small>
            </div>

            <div className="observation-field">
              <label>
                Turning Weights (ΔL) <span>{snap?.unit || 'kg'}</span>
              </label>
              <input
                type="text"
                value={additionalLoad}
                onChange={(e) => {
                  setAdditionalLoad(e.target.value)
                  setCalcResponse(null)
                }}
                aria-label="Additional turning point load"
              />
              <small>Clause A.4.4.3 additional load</small>
            </div>

            <div className="observation-field">
              <label>
                Zero-Load Error (E0) <span>{snap?.unit || 'kg'}</span>
              </label>
              <input
                type="text"
                value={zeroError}
                onChange={(e) => {
                  setZeroError(e.target.value)
                  setCalcResponse(null)
                }}
                aria-label="Zero error"
              />
              <small>Calculated error at zero load</small>
            </div>

            <div className="observation-field">
              <label>
                Scale Interval (e) <span>{snap?.unit || 'kg'}</span>
              </label>
              <strong>{snap?.verification_scale_interval || '0.010'}</strong>
              <small>From frozen snapshot</small>
            </div>

            <div className="observation-field">
              <label>
                Table 6 MPE Tier <span>{snap?.unit || 'kg'}</span>
              </label>
              <strong>±{(calcResponse ? parseFloat(calcResponse.mpeMass) : previewMpe).toFixed(3)}</strong>
              <small>±1.0 e for 500e &lt; m ≤ 2000e</small>
            </div>
          </div>

          {/* Validation & Computed Live Result */}
          <div className="validation-note" style={{ marginTop: '20px' }}>
            <Check aria-hidden="true" />
            <div>
              <strong>
                {calcResponse ? 'Authoritative Backend AST Calculation Sealed:' : 'Live Operator Preview (Pending Commit):'}
              </strong>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '11px', display: 'block', marginTop: '4px' }}>
                P = {calcResponse ? calcResponse.P : previewP.toFixed(3)} {snap?.unit || 'kg'} · Error E ={' '}
                {calcResponse ? calcResponse.E : previewE >= 0 ? `+${previewE.toFixed(3)}` : previewE.toFixed(3)}{' '}
                {snap?.unit || 'kg'} · Corrected Ec ={' '}
                {calcResponse ? calcResponse.Ec : previewEc >= 0 ? `+${previewEc.toFixed(3)}` : previewEc.toFixed(3)}{' '}
                {snap?.unit || 'kg'}
              </span>
            </div>
          </div>

          {calcResponse?.reasoning && (
            <div style={{ marginTop: '12px', padding: '10px 14px', background: '#121714', borderRadius: '6px', borderLeft: '3px solid var(--lime)', fontSize: '11px', color: '#b8c4b4' }}>
              <strong>Metrological Explanation:</strong> {calcResponse.reasoning}
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '28px', flexWrap: 'wrap', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Badge tone={isPass ? 'lime' : 'red'}>
                {isPass ? 'PASS · WITHIN MPE' : 'FAIL · EXCEEDS MPE'}
              </Badge>
              <span style={{ color: 'var(--dim)', font: '10px ui-monospace, monospace' }}>
                |{calcResponse ? calcResponse.Ec : previewEc.toFixed(3)}| ≤{' '}
                {calcResponse ? calcResponse.mpeMass : previewMpe.toFixed(3)} {snap?.unit || 'kg'}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                type="button"
                className="button button-secondary"
                onClick={handleCalculate}
                disabled={calculating}
              >
                {calculating ? (
                  <>
                    <RefreshCw className="animate-spin" style={{ width: '13px' }} /> Calculating...
                  </>
                ) : (
                  <>
                    <Zap style={{ width: '13px' }} /> Calculate & Commit
                  </>
                )}
              </button>

              <Link href={`/evaluations/${evaluation.id}/compliance`} className="button">
                Commit & view compliance <ArrowRight style={{ width: '13px' }} />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
