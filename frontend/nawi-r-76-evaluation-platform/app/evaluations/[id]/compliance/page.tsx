'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronDown,
  GitBranch,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationCompliancePage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]
  const inst = evaluation.instrument

  const [expandedProcedure, setExpandedProcedure] = useState<string>('P-01')

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={4} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>05</span>Deterministic Compliance Engine
          </div>
          <h1>Compliance Decisions & Calculations</h1>
          <p>
            Pure deterministic legal metrology evaluation. Compliance decisions are computed by
            verified Python Decimal AST rules evaluated against OIML R 76 Table 6 limits without AI heuristics.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/evidence`} className="button">
            Inspect evidence trace <GitBranch />
          </Link>
        </div>
      </div>

      {/* Compliance Overview Banner */}
      <div className="decision-banner">
        <div className="decision-icon" aria-hidden="true">
          <ShieldCheck />
        </div>
        <div>
          <Badge tone="lime">OVERALL COMPLIANT</Badge>
          <h2>All intrinsic error tolerances satisfied.</h2>
          <p>
            {inst.modelName} (SN: {inst.serialNumber}) complies with OIML R 76-1:2006 (E) Class III requirements.
          </p>
        </div>
        <strong>
          {evaluation.passedProcedures} / {evaluation.totalProcedures}
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
              <h2>Weighing Performance (Point 1: 10.000 kg)</h2>
            </div>
            <Badge tone="lime">Within Tolerance</Badge>
          </div>

          <div className="equation">
            <div>
              <span>CALCULATED ERROR (Ec)</span>
              <strong>+0.002 kg</strong>
            </div>
            <b>≤</b>
            <div>
              <span>TABLE 6 MPE</span>
              <strong>±0.010 kg</strong>
            </div>
            <div className="equation-pass">
              <Check aria-hidden="true" />
              <span>PASS</span>
            </div>
          </div>

          <div className="calc-path">
            <div>
              <span>1. Observed Indication (I)</span>
              <strong>10.000 kg</strong>
            </div>
            <div>
              <span>2. Half Scale Interval (+ ½ e)</span>
              <strong>+0.005 kg (verification interval e = 0.010 kg)</strong>
            </div>
            <div>
              <span>3. Additional Turning Load (- ΔL)</span>
              <strong>-0.003 kg</strong>
            </div>
            <div style={{ background: '#182017', padding: '10px' }}>
              <span>4. Indication Prior to Rounding (P = I + ½e - ΔL)</span>
              <strong style={{ color: 'var(--lime)' }}>10.002 kg</strong>
            </div>
            <div>
              <span>5. Calibrated Test Load (L)</span>
              <strong>10.000 kg</strong>
            </div>
            <div>
              <span>6. Gross Error (E = P - L)</span>
              <strong>+0.002 kg</strong>
            </div>
            <div>
              <span>7. Error at Zero Load (E0)</span>
              <strong>+0.000 kg</strong>
            </div>
            <div className="path-result" style={{ background: '#1c261a', padding: '12px' }}>
              <span>8. Final Corrected Error (Ec = E - E0)</span>
              <strong>+0.002 kg</strong>
            </div>
          </div>

          <div style={{ marginTop: '20px', padding: '14px', background: '#0e1210', borderRadius: '8px', border: '1px solid var(--line)' }}>
            <span className="eyebrow lime-text">Authoritative Compliance Criterion</span>
            <p style={{ color: 'var(--muted)', fontSize: '11px', margin: '6px 0 0', lineHeight: 1.5 }}>
              Under OIML R 76-1:2006 Table 6 for Class III: for test loads between 500e and 2,000e (5 kg to 20 kg),
              maximum permissible error is ±1.0 e = ±0.010 kg. Since |+0.002 kg| ≤ 0.010 kg, margin = +0.008 kg inside limit.
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
            <strong>2006-01 (Active)</strong>
          </div>
          <div className="detail-row">
            <span>Execution Timestamp</span>
            <strong>{new Date(evaluation.updatedAt).toUTCString()}</strong>
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
            <span>Certified Operator</span>
            <strong>{evaluation.operatorName}</strong>
          </div>

          <div className="deterministic" style={{ marginTop: '24px' }}>
            <Zap aria-hidden="true" /> Zero AI decision-making. Pure deterministic legal metrology rules.
          </div>

          <Link
            href={`/evaluations/${evaluation.id}/evidence`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', marginTop: '20px' }}
          >
            Inspect evidence chain <ArrowRight />
          </Link>
        </aside>
      </div>
    </div>
  )
}
