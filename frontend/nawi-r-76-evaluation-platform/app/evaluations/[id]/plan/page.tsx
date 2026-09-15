'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Play,
  SlidersHorizontal,
  TestTube2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { CANONICAL_PROCEDURES, MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationPlanPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]

  const [openedWhy, setOpenedWhy] = useState<string | null>(null)

  const applicableTests = CANONICAL_PROCEDURES.filter((p) =>
    evaluation.instrument.isMultipleRange
      ? p.applicableToMultipleRange
      : p.applicableToSingleRange
  )

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={2} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>02 & 03</span>Generated Execution Plan
          </div>
          <h1>Applicable R-76 Test Plan</h1>
          <p>
            Authoritative test procedures resolved deterministically by the Applicability Engine from the
            frozen snapshot of <strong>{evaluation.instrument.modelName}</strong>.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/configuration`} className="button button-secondary">
            <SlidersHorizontal /> View configuration
          </Link>
          <Link href={`/evaluations/${evaluation.id}/tests/test-wp-01`} className="button">
            Start guided test <Play />
          </Link>
        </div>
      </div>

      <div className="plan-layout">
        {/* Main Test List Panel */}
        <div className="panel plan-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow lime-text">Execution Schedule</span>
              <h2>
                {applicableTests.length} Applicable Procedures <span className="slash">/</span>{' '}
                {evaluation.instrument.isMultipleRange ? 'Multiple Range' : 'Single Range'}
              </h2>
            </div>
            <Badge tone="lime">Locked to Snapshot</Badge>
          </div>

          <div className="plan-items-container">
            {applicableTests.map((proc, index) => {
              const isWhyOpen = openedWhy === proc.id
              const isFirst = index === 0

              return (
                <div className="plan-item" key={proc.id} style={{ position: 'relative' }}>
                  <span className="plan-num">{String(index + 1).padStart(2, '0')}</span>
                  <div className="plan-icon" aria-hidden="true">
                    <TestTube2 />
                  </div>
                  <div className="plan-copy">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong>{proc.name}</strong>
                      <button
                        type="button"
                        className="why"
                        onClick={() => setOpenedWhy(isWhyOpen ? null : proc.id)}
                        aria-label={`Why is ${proc.name} applicable?`}
                        title="Why is this procedure applicable?"
                      >
                        <CircleHelp />
                      </button>
                    </div>
                    <span>OIML R 76-1:2006 · Clause {proc.r76Ref}</span>
                    <p>{proc.description}</p>

                    {isWhyOpen && (
                      <div className="why-detail" style={{ position: 'static', margin: '8px 0 12px' }}>
                        <span>R-76 APPLICABILITY JUSTIFICATION</span>
                        <p>
                          <strong>Clause {proc.r76Ref}:</strong> {proc.whyApplicable}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="plan-state">
                    <Badge tone={isFirst ? 'lime' : proc.status === 'IMPLEMENTED' ? 'neutral' : 'outline'}>
                      {isFirst ? 'In Progress' : proc.status === 'IMPLEMENTED' ? 'Queued' : 'Applicability Only'}
                    </Badge>
                    <span>{isFirst ? 'Active' : `${index * 6 + 8} min`}</span>
                  </div>

                  <Link
                    href={`/evaluations/${evaluation.id}/tests/test-wp-01`}
                    className="button button-quiet"
                    aria-label={`Execute ${proc.name}`}
                    style={{ padding: '6px' }}
                  >
                    <ChevronRight className="plan-chevron" />
                  </Link>
                </div>
              )
            })}
          </div>
        </div>

        {/* Readiness Aside */}
        <aside className="panel readiness-panel">
          <span className="eyebrow">Execution Readiness</span>
          <h2>Pre-test validation</h2>

          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Configuration snapshot locked</span>
          </div>
          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Rule version validated (2006-01)</span>
          </div>
          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Table 6 MPE steps precomputed</span>
          </div>
          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Standard weights calibration verified</span>
          </div>

          <div className="config-divider" />

          <div className="ready-stat">
            <span>Applicable tests</span>
            <strong>{applicableTests.length} procedures</strong>
          </div>
          <div className="ready-stat">
            <span>Implemented in Phase 2</span>
            <strong style={{ color: 'var(--lime)' }}>Weighing, Eccentricity, Repeatability</strong>
          </div>

          <Link
            href={`/evaluations/${evaluation.id}/tests/test-wp-01`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', marginTop: '20px' }}
          >
            Launch guided test <Play />
          </Link>
        </aside>
      </div>
    </div>
  )
}
