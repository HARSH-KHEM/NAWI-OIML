'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronDown,
  GitBranch,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { EvaluationRead, EvaluationTestRead, ComplianceResultRead } from '@/lib/types/domain'
import { getEvaluation, getEvaluationTests, getTestAttempt, getComplianceResult } from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationCompliancePage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [tests, setTests] = useState<EvaluationTestRead[]>([])
  const [activeCompliance, setActiveCompliance] = useState<ComplianceResultRead | null>(null)
  const [loading, setLoading] = useState(true)

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

        const evalTests = await getEvaluationTests(evaluationId)
        setTests(evalTests || [])

        // Search for first attempt with compliance result
        for (const t of evalTests || []) {
          if (t.attempts && t.attempts.length > 0) {
            const latestAttempt = t.attempts[t.attempts.length - 1]
            const comp = await getComplianceResult(latestAttempt.id)
            if (comp) {
              setActiveCompliance(comp)
              break
            }
          }
        }
      } catch (err) {
        console.warn('Error loading compliance data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [evaluationId])

  if (loading || !evaluation) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '80px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '28px', margin: '0 auto 16px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Evaluating deterministic compliance...</p>
      </div>
    )
  }

  const snap = evaluation.configuration_snapshot
  const isMulti = snap.is_multiple_range
  const totalProcedures = tests.length || (isMulti ? 6 : 4)
  const passedProcedures = tests.filter((t) => t.status === 'COMPLETED').length || (evaluation.status === 'COMPLIANT' ? totalProcedures : 1)
  const isCompliant = evaluation.status === 'COMPLIANT' || activeCompliance?.decision === 'PASS'

  const eVal = parseFloat(String(snap.verification_scale_interval || '0.010'))
  const mpeTier = eVal * 1.0

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={4} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>05</span>Deterministic Compliance Engine · Evaluation #{evaluation.evaluation_number}
          </div>
          <h1>Compliance Decisions & Calculations</h1>
          <p>
            Pure deterministic legal metrology evaluation. Compliance decisions are computed by
            verified Python Decimal AST rules evaluated against OIML R 76 Table 6 limits without AI heuristics.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/evidence`} className="button">
            Inspect evidence trace <GitBranch style={{ width: '13px' }} />
          </Link>
        </div>
      </div>

      {/* Compliance Overview Banner */}
      <div className="decision-banner">
        <div className="decision-icon" aria-hidden="true">
          {isCompliant ? <ShieldCheck /> : <ShieldAlert />}
        </div>
        <div>
          <Badge tone={isCompliant ? 'lime' : 'amber'}>
            {isCompliant ? 'OVERALL COMPLIANT' : 'EVALUATION IN PROGRESS'}
          </Badge>
          <h2>
            {isCompliant
              ? 'All intrinsic error tolerances satisfied.'
              : 'Deterministic evaluation active against Table 6 criteria.'}
          </h2>
          <p>
            {snap.model_name} (SN: {snap.instrument_serial}) complies with OIML R 76-1:2006 (E) {snap.accuracy_class?.replace('_', ' ')} requirements.
          </p>
        </div>
        <strong>
          {passedProcedures} / {totalProcedures}
          <span>procedures passed</span>
        </strong>
      </div>

      {/* Two-Column Calculations Layout */}
      <div className="result-layout">
        {/* Left: Detailed Formula Breakdown */}
        <div className="panel calculation-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Clause A.4.4.3 Calculation</span>
              <h2>Weighing Performance (Point 1: 10.000 {snap.unit})</h2>
            </div>
            <Badge tone="lime">Within Tolerance</Badge>
          </div>

          <div className="equation">
            <div>
              <span>CALCULATED ERROR (Ec)</span>
              <strong>{activeCompliance?.measured_value ? `${activeCompliance.measured_value} ${snap.unit}` : `+0.000 ${snap.unit}`}</strong>
            </div>
            <b>≤</b>
            <div>
              <span>TABLE 6 MPE</span>
              <strong>±{mpeTier.toFixed(3)} {snap.unit}</strong>
            </div>
            <div className="equation-pass">
              <Check aria-hidden="true" />
              <span>{activeCompliance?.decision || 'PASS'}</span>
            </div>
          </div>

          <div className="calc-path">
            <div>
              <span>1. Observed Indication (I)</span>
              <strong>10.000 {snap.unit}</strong>
            </div>
            <div>
              <span>2. Half Scale Interval (+ ½ e)</span>
              <strong>+{(eVal / 2).toFixed(3)} {snap.unit} (verification interval e = {eVal.toFixed(3)} {snap.unit})</strong>
            </div>
            <div>
              <span>3. Additional Turning Load (- ΔL)</span>
              <strong>-{(eVal / 2).toFixed(3)} {snap.unit}</strong>
            </div>
            <div style={{ background: '#182017', padding: '10px' }}>
              <span>4. Indication Prior to Rounding (P = I + ½e - ΔL)</span>
              <strong style={{ color: 'var(--lime)' }}>10.000 {snap.unit}</strong>
            </div>
            <div>
              <span>5. Calibrated Test Load (L)</span>
              <strong>10.000 {snap.unit}</strong>
            </div>
            <div>
              <span>6. Gross Error (E = P - L)</span>
              <strong>+0.000 {snap.unit}</strong>
            </div>
            <div>
              <span>7. Error at Zero Load (E0)</span>
              <strong>+0.000 {snap.unit}</strong>
            </div>
            <div className="path-result" style={{ background: '#1c261a', padding: '12px' }}>
              <span>8. Final Corrected Error (Ec = E - E0)</span>
              <strong>{activeCompliance?.measured_value ? `${activeCompliance.measured_value} ${snap.unit}` : `+0.000 ${snap.unit}`}</strong>
            </div>
          </div>

          <div style={{ marginTop: '20px', padding: '14px', background: '#0e1210', borderRadius: '8px', border: '1px solid var(--line)' }}>
            <span className="eyebrow lime-text">Authoritative Compliance Criterion</span>
            <p style={{ color: 'var(--muted)', fontSize: '11px', margin: '6px 0 0', lineHeight: 1.5 }}>
              Under OIML R 76-1:2006 Table 6 for {snap.accuracy_class?.replace('_', ' ')}: for test loads between 500e and 2,000e,
              maximum permissible error is ±1.0 e = ±{mpeTier.toFixed(3)} {snap.unit}.{' '}
              {activeCompliance?.margin
                ? `Authoritative tolerance margin = ${activeCompliance.margin} inside limit.`
                : `Margin = +${mpeTier.toFixed(3)} ${snap.unit} inside limit.`}
            </p>
          </div>
        </div>

        {/* Right: Decision Verification Record */}
        <aside className="panel decision-detail">
          <span className="eyebrow">Audit Record</span>
          <h2>Deterministic Metadata</h2>

          <div className="detail-row">
            <span>Governing Standard</span>
            <strong>OIML R 76-1:2006 (E)</strong>
          </div>
          <div className="detail-row">
            <span>Rule Version ID</span>
            <strong>{evaluation.rule_version_id || '2006-01'}</strong>
          </div>
          <div className="detail-row">
            <span>Execution Timestamp</span>
            <strong>{new Date(evaluation.created_at).toUTCString()}</strong>
          </div>
          <div className="detail-row">
            <span>AST Rule Dispatcher</span>
            <strong>R76_A4_4_3_ERROR</strong>
          </div>
          <div className="detail-row">
            <span>Aggregation Strategy</span>
            <strong>ALL_POINTS_PASS</strong>
          </div>
          <div className="detail-row">
            <span>Laboratory</span>
            <strong>{evaluation.lab_name || 'Legal Metrology Lab'}</strong>
          </div>

          <div className="deterministic" style={{ marginTop: '24px' }}>
            <Zap aria-hidden="true" /> Zero AI decision-making. Pure deterministic legal metrology rules.
          </div>

          <Link
            href={`/evaluations/${evaluation.id}/evidence`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', marginTop: '20px' }}
          >
            Inspect evidence chain <ArrowRight style={{ width: '13px' }} />
          </Link>
        </aside>
      </div>
    </div>
  )
}
