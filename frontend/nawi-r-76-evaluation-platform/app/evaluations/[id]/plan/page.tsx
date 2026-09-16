'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Play,
  RefreshCw,
  SlidersHorizontal,
  TestTube2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { EvaluationRead, EvaluationPlanResponse, EvaluationTestRead } from '@/lib/types/domain'
import { getEvaluation, getEvaluationPlan, generateEvaluationPlan } from '@/lib/api/services'
import { CANONICAL_PROCEDURES, MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationPlanPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [plan, setPlan] = useState<EvaluationPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [openedWhy, setOpenedWhy] = useState<string | null>(null)

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

        let planData = await getEvaluationPlan(evaluationId)
        if (!planData || !planData.tests || planData.tests.length === 0) {
          // Attempt to generate plan if not generated yet
          try {
            planData = await generateEvaluationPlan(evaluationId)
          } catch {
            // keep whatever we have
          }
        }
        setPlan(planData)
      } catch (err) {
        console.warn('Error loading plan:', err)
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
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Generating authoritative R-76 test plan...</p>
      </div>
    )
  }

  const snap = evaluation.configuration_snapshot
  const isMulti = snap.is_multiple_range

  // Use live tests from plan if available, otherwise fallback to canonical procedures
  const liveTests: EvaluationTestRead[] = plan?.tests && plan.tests.length > 0 ? plan.tests : []
  const hasLiveTests = liveTests.length > 0

  const fallbackTests = CANONICAL_PROCEDURES.filter((p) =>
    isMulti ? p.applicableToMultipleRange : p.applicableToSingleRange
  )

  const firstTestId = hasLiveTests ? liveTests[0].id : 'test-wp-01'
  const applicableCount = hasLiveTests ? liveTests.length : fallbackTests.length

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={2} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>02 & 03</span>Generated Execution Plan · Evaluation #{evaluation.evaluation_number}
          </div>
          <h1>Applicable R-76 Test Plan</h1>
          <p>
            Authoritative test procedures resolved deterministically by the Applicability Engine from the
            frozen snapshot of <strong>{snap.model_name}</strong> (SN: {snap.instrument_serial}).
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/configuration`} className="button button-secondary">
            <SlidersHorizontal style={{ width: '13px' }} /> View configuration
          </Link>
          <Link href={`/evaluations/${evaluation.id}/tests/${firstTestId}`} className="button">
            Start guided test <Play style={{ width: '13px' }} />
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
                {applicableCount} Applicable Procedures <span className="slash">/</span>{' '}
                {isMulti ? `Multiple Range (${snap.ranges?.length || 2} ranges)` : 'Single Range'}
              </h2>
            </div>
            <Badge tone="lime">Locked to Snapshot</Badge>
          </div>

          <div className="plan-items-container">
            {hasLiveTests
              ? liveTests.map((test, index) => {
                  const isWhyOpen = openedWhy === test.id
                  const isFirst = index === 0

                  return (
                    <div className="plan-item" key={test.id} style={{ position: 'relative' }}>
                      <span className="plan-num">{String(test.sequence || index + 1).padStart(2, '0')}</span>
                      <div className="plan-icon" aria-hidden="true">
                        <TestTube2 />
                      </div>
                      <div className="plan-copy">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <strong>{test.title || test.test_code}</strong>
                          {test.range_reference && (
                            <Badge tone="lime">{test.range_reference}</Badge>
                          )}
                          <Badge tone="neutral">{test.scope_type || 'INSTRUMENT'}</Badge>
                          <button
                            type="button"
                            className="why"
                            onClick={() => setOpenedWhy(isWhyOpen ? null : test.id)}
                            aria-label={`Why is ${test.title} applicable?`}
                            title="Why is this procedure applicable?"
                          >
                            <CircleHelp style={{ width: '14px' }} />
                          </button>
                        </div>
                        <span>OIML R 76-1:2006 · Clause {test.r76_reference || 'A.4'} · Code: {test.test_code}</span>
                        <p>{test.applicability_reason}</p>

                        {isWhyOpen && (
                          <div className="why-detail" style={{ position: 'static', margin: '8px 0 12px' }}>
                            <span>R-76 APPLICABILITY JUSTIFICATION</span>
                            <p>
                              <strong>Clause {test.r76_reference}:</strong> {test.applicability_reason}
                            </p>
                            {test.scope_type === 'RANGE' && test.range_reference && (
                              <p style={{ marginTop: '4px', color: 'var(--lime)' }}>
                                Evaluated independently for partial range {test.range_reference} under Clause A.4.4.4.
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="plan-state">
                        <Badge
                          tone={
                            test.status === 'COMPLETED'
                              ? 'lime'
                              : test.status === 'IN_PROGRESS' || isFirst
                              ? 'amber'
                              : test.implementation_status === 'IMPLEMENTED'
                              ? 'neutral'
                              : 'outline'
                          }
                        >
                          {test.status === 'COMPLETED'
                            ? 'Completed'
                            : test.status === 'IN_PROGRESS' || isFirst
                            ? 'In Progress'
                            : test.implementation_status === 'IMPLEMENTED'
                            ? 'Queued'
                            : 'Applicability Only'}
                        </Badge>
                        <span>{test.implementation_status === 'IMPLEMENTED' ? 'Lab Ready' : 'Normative'}</span>
                      </div>

                      <Link
                        href={`/evaluations/${evaluation.id}/tests/${test.id}`}
                        className="button button-quiet"
                        aria-label={`Execute ${test.title}`}
                        style={{ padding: '6px' }}
                      >
                        <ChevronRight className="plan-chevron" />
                      </Link>
                    </div>
                  )
                })
              : fallbackTests.map((proc, index) => {
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
                            <CircleHelp style={{ width: '14px' }} />
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
            <span>Rule version validated ({evaluation.rule_version_id || '2006-01'})</span>
          </div>
          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Table 6 MPE limits resolved</span>
          </div>
          <div className="ready-row">
            <Check style={{ color: 'var(--lime)', width: '14px' }} />
            <span>Standard weights calibrated</span>
          </div>

          <div className="config-divider" />

          <div className="ready-stat">
            <span>Applicable procedures</span>
            <strong>{applicableCount} procedures</strong>
          </div>
          <div className="ready-stat">
            <span>Range Mode</span>
            <strong>{isMulti ? 'Multiple Range' : 'Single Range'}</strong>
          </div>
          <div className="ready-stat">
            <span>Implemented in Phase 2</span>
            <strong style={{ color: 'var(--lime)' }}>Weighing, Eccentricity, Repeatability</strong>
          </div>

          <Link
            href={`/evaluations/${evaluation.id}/tests/${firstTestId}`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', marginTop: '20px' }}
          >
            Launch guided test <Play style={{ width: '13px' }} />
          </Link>
        </aside>
      </div>
    </div>
  )
}
