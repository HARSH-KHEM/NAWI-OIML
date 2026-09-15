'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronDown,
  FileCheck2,
  GitBranch,
  ShieldCheck,
  Upload,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationEvidencePage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]
  const inst = evaluation.instrument

  const [activeStep, setActiveStep] = useState<number | null>(0)

  // Full 8-tier explainable trace chain from Section 9
  const traceNodes = [
    {
      step: 'PASS',
      title: 'Compliance Decision',
      subtitle: 'Table 6 Permissible Error Tolerances Satisfied',
      details: [
        { label: 'Decision', value: 'PASS / COMPLIANT' },
        { label: 'Evaluation Number', value: evaluation.evaluationNumber },
        { label: 'Evaluated By', value: 'Rule Engine AST (Deterministic)' },
        { label: 'Timestamp', value: '14 Sep 2026, 11:45:00 UTC' },
      ],
      justification: 'All tested load points in weighing performance, eccentricity, and repeatability remained within the maximum permissible errors.',
    },
    {
      step: '01',
      title: 'Governing Metrological Criterion',
      subtitle: 'OIML R 76-1:2006 Table 6 MPE Tier',
      details: [
        { label: 'Accuracy Class', value: 'Class III (Medium Accuracy)' },
        { label: 'Load Tier', value: '500 e < m ≤ 2,000 e (5.000 kg to 20.000 kg)' },
        { label: 'Tolerance Limit', value: '±1.0 e = ±0.010 kg' },
        { label: 'Aggregation Mode', value: 'ALL_POINTS_PASS' },
      ],
      justification: 'The applied test load L = 10.000 kg falls into the intermediate load tier with MPE = ±1.0 e.',
    },
    {
      step: '02',
      title: 'Deterministic Calculation Output',
      subtitle: 'Pure Decimal AST Formula Evaluation',
      details: [
        { label: 'Formula Reference', value: 'OIML R 76-1:2006 Clause A.4.4.3' },
        { label: 'Calculated Indication (P)', value: '10.002 kg' },
        { label: 'Gross Error (E)', value: '+0.002 kg' },
        { label: 'Corrected Error (Ec)', value: '+0.002 kg' },
      ],
      justification: 'Computed via P = I + ½e - ΔL = 10.000 + 0.005 - 0.003 = 10.002 kg. Corrected error Ec = E - E0 = 0.002 - 0.000 = +0.002 kg.',
    },
    {
      step: '03',
      title: 'Raw Laboratory Observations',
      subtitle: 'Immutable Physical Measurements Captured in Laboratory',
      details: [
        { label: 'Applied Load (L)', value: '10.000 kg (Calibrated Standard Weights)' },
        { label: 'Observed Indication (I)', value: '10.000 kg' },
        { label: 'Additional Load (ΔL)', value: '0.003 kg' },
        { label: 'Zero Error (E0)', value: '+0.000 kg' },
      ],
      justification: 'Raw observations entered by certified laboratory operator. Immutable and sealed with SHA-256 integrity hash.',
    },
    {
      step: '04',
      title: 'Test Attempt Record',
      subtitle: 'Execution Attempt #1 (Non-Destructive Retest Model)',
      details: [
        { label: 'Attempt Number', value: 'Attempt 01 (Initial Execution)' },
        { label: 'Status', value: 'COMPLETED' },
        { label: 'Operator', value: evaluation.operatorName },
        { label: 'Retest Superseded', value: 'None (Attempt passed on initial loading)' },
      ],
      justification: 'First execution attempt succeeded. If retesting had been required, Attempt 1 history would remain permanently preserved.',
    },
    {
      step: '05',
      title: 'Test Procedure Instance',
      subtitle: 'Clause A.4.4 Weighing Performance Test',
      details: [
        { label: 'Test Code', value: 'WEIGHING_PERFORMANCE' },
        { label: 'Clause Reference', value: 'OIML R 76-1:2006 (E) A.4.4' },
        { label: 'Scope', value: 'Instrument (Single-Range Continuous)' },
        { label: 'Sequence Position', value: '#10 in execution schedule' },
      ],
      justification: 'Mandatory primary performance evaluation under Section 3.10 and Annex A.4.4.',
    },
    {
      step: '06',
      title: 'Frozen Configuration Snapshot',
      subtitle: 'Immutable Metrological Parameters Locked At Evaluation Initialization',
      details: [
        { label: 'Model', value: inst.modelName },
        { label: 'Max / Min Capacity', value: `Max ${inst.maxCapacity} ${inst.unit} / Min ${inst.minCapacity} ${inst.unit}` },
        { label: 'Scale Intervals', value: `e = ${inst.verificationScaleInterval} ${inst.unit}, d = ${inst.actualScaleInterval} ${inst.unit}` },
        { label: 'Capabilities', value: 'Single Range · Subtractive Tare · Electronic' },
      ],
      justification: 'Snapshot sealed at 2026-09-14T09:30:00Z. Instrument catalogue edits never overwrite this record.',
    },
    {
      step: '07',
      title: 'Standard Rule Version',
      subtitle: 'Governing Legal Metrology Standard & AST Dispatcher',
      details: [
        { label: 'Standard', value: 'OIML R 76-1:2006 (E)' },
        { label: 'Rule Version ID', value: '2006-01 (Active)' },
        { label: 'Rule Hash', value: 'sha256:7f3b89e2104a... (Deterministic AST)' },
        { label: 'Compliance Engine', value: 'Fail-Closed Metrological Evaluator' },
      ],
      justification: 'Root regulatory authority for all type evaluations conducted on this platform.',
    },
  ]

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={5} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>06</span>Explainable Audit Trail
          </div>
          <h1>Evidence Traceability Graph</h1>
          <p>
            An unbroken regulatory compliance chain. In legal metrology, a decision is only valid if
            every intermediate calculation, raw measurement, and configuration parameter can be inspected back to the governing rule.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/report`} className="button">
            View technical report <ArrowRight />
          </Link>
        </div>
      </div>

      <div className="panel evidence-panel">
        <div className="evidence-head">
          <div className="decision-icon" aria-hidden="true">
            <FileCheck2 />
          </div>
          <div>
            <Badge tone="lime">Trace Verified & Sealed</Badge>
            <h2>{evaluation.evaluationNumber} · Complete Trace Chain</h2>
            <p>From compliance decision to governing OIML R 76-1:2006 clause</p>
          </div>
        </div>

        <div className="evidence-chain" style={{ gridTemplateColumns: '1fr', gap: '16px', paddingTop: '24px' }}>
          {traceNodes.map((node, i) => {
            const isOpen = activeStep === i
            return (
              <div
                key={node.title}
                className="panel"
                style={{
                  background: isOpen ? '#141c16' : '#111512',
                  borderColor: isOpen ? 'var(--lime-dark)' : 'var(--line)',
                  padding: '18px 24px',
                  transition: 'all 0.2s ease',
                }}
              >
                <div
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
                  onClick={() => setActiveStep(isOpen ? null : i)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div className="evidence-marker">
                      <span>{node.step === 'PASS' ? <Check /> : node.step}</span>
                    </div>
                    <div>
                      <strong style={{ fontSize: '14px', color: 'var(--warm)', display: 'block' }}>
                        {node.title}
                      </strong>
                      <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                        {node.subtitle}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Badge tone="lime">Verified</Badge>
                    <ChevronDown
                      style={{
                        width: '16px',
                        color: 'var(--dim)',
                        transform: isOpen ? 'rotate(180deg)' : 'none',
                        transition: 'transform 0.2s',
                      }}
                    />
                  </div>
                </div>

                {isOpen && (
                  <div style={{ marginTop: '18px', paddingTop: '16px', borderTop: '1px solid var(--line)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                      {node.details.map((d) => (
                        <div key={d.label} style={{ background: '#0b0e0c', padding: '10px 14px', borderRadius: '7px', border: '1px solid var(--line)' }}>
                          <span style={{ fontSize: '9px', color: 'var(--dim)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block' }}>
                            {d.label}
                          </span>
                          <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace', display: 'block', marginTop: '4px' }}>
                            {d.value}
                          </strong>
                        </div>
                      ))}
                    </div>

                    <p style={{ color: '#b8c4b4', fontSize: '11px', lineHeight: 1.5, background: '#192218', padding: '12px 16px', borderRadius: '7px', borderLeft: '3px solid var(--lime)' }}>
                      <strong>Audit Note:</strong> {node.justification}
                    </p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
