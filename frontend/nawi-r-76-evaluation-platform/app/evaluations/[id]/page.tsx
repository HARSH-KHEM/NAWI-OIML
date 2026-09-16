'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  ClipboardCheck,
  FileCheck2,
  Gauge,
  GitBranch,
  Play,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
  TestTube2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { EvaluationRead, EvaluationPlanResponse } from '@/lib/types/domain'
import { getEvaluation, getEvaluationPlan, getEvaluationTests } from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationDetailPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [plan, setPlan] = useState<EvaluationPlanResponse | null>(null)
  const [firstTestId, setFirstTestId] = useState<string>('test-wp-01')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const evalData = await getEvaluation(evaluationId)
        if (evalData) {
          setEvaluation(evalData)
        } else {
          // Fallback mock
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

        // Fetch plan and tests
        const [planData, tests] = await Promise.all([
          getEvaluationPlan(evaluationId),
          getEvaluationTests(evaluationId),
        ])

        if (planData) {
          setPlan(planData)
          if (planData.tests && planData.tests.length > 0) {
            setFirstTestId(planData.tests[0].id)
          }
        } else if (tests && tests.length > 0) {
          setFirstTestId(tests[0].id)
        }
      } catch (err) {
        console.warn('Failed to load evaluation details:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [evaluationId])

  if (loading || !evaluation) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '80px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '28px', margin: '0 auto 16px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Loading evaluation hub...</p>
      </div>
    )
  }

  const snap = evaluation.configuration_snapshot
  const isMulti = snap.is_multiple_range
  const totalProcedures = plan?.total_tests || (isMulti ? 10 : 9)
  const applicableProcedures = plan?.applicable_tests_count || (isMulti ? 6 : 4)

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      {/* 01-07 Pipeline Stepper */}
      <Pipeline current={1} evaluationId={evaluation.id} />

      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>{evaluation.evaluation_number}</span>Type Evaluation Hub
          </div>
          <h1>{snap.model_name || 'Weighing Instrument'}</h1>
          <p>
            {snap.manufacturer} · Standard: {evaluation.rule_version_id || 'OIML R 76-1:2006'} · Laboratory: {evaluation.lab_name || 'Legal Metrology Lab'}
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button">
            View generated test plan <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>
      </div>

      {/* Instrument Metrology Strip */}
      <div className="instrument-strip">
        <div className="instrument-symbol" aria-hidden="true">
          <Gauge />
        </div>
        <div>
          <span className="eyebrow">Frozen Snapshot / {snap.instrument_serial}</span>
          <h2>
            {snap.model_name} <Badge tone={evaluation.status === 'COMPLIANT' ? 'lime' : evaluation.status === 'NON_COMPLIANT' ? 'red' : 'amber'}>{evaluation.status}</Badge>
          </h2>
          <p>
            Non-automatic weighing instrument · {snap.accuracy_class?.replace('_', ' ')} ·{' '}
            {isMulti ? `Multiple Range (${snap.ranges?.length || 2} ranges)` : 'Single Range'}
          </p>
        </div>
        <div className="strip-spec">
          <span>Max Capacity</span>
          <strong>{snap.max_capacity} {snap.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Min Capacity</span>
          <strong>{snap.min_capacity} {snap.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Scale Interval (e)</span>
          <strong>{snap.verification_scale_interval} {snap.unit}</strong>
        </div>
      </div>

      {/* Evaluation Workflow Navigation Cards */}
      <div className="editorial-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginTop: '28px' }}>
        {/* Card 1: Configuration Snapshot */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 01</span>
            <SlidersHorizontal style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            Configuration Snapshot
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            Inspect frozen metrological parameters, tare mechanism, zero setting, and receptor geometry.
          </p>
          <Link href={`/evaluations/${evaluation.id}/configuration`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            Inspect configuration <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>

        {/* Card 2: Generated Test Plan */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 02 & 03</span>
            <ClipboardCheck style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            Applicable Test Plan
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            {applicableProcedures} rule-derived procedures scheduled based on instrument configuration.
          </p>
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            Open test schedule <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>

        {/* Card 3: Guided Laboratory Execution */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 04</span>
            <TestTube2 style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            Guided Execution Workspace
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            Record laboratory observations (Load, Indication, ΔL, Zero Error) with real-time validation.
          </p>
          <Link href={`/evaluations/${evaluation.id}/tests/${firstTestId}`} className="button" style={{ marginTop: 'auto' }}>
            Enter test workspace <Play style={{ width: '13px' }} />
          </Link>
        </div>

        {/* Card 4: Compliance & Calculations */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 05</span>
            <ShieldCheck style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            Compliance Decisions
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            Deterministic evaluation against OIML R 76 Table 6 maximum permissible errors.
          </p>
          <Link href={`/evaluations/${evaluation.id}/compliance`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            View calculations <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>

        {/* Card 5: Evidence Traceability */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 06</span>
            <GitBranch style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            Evidence Traceability Graph
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            Explainable audit chain connecting final decisions to raw observations and rule clauses.
          </p>
          <Link href={`/evaluations/${evaluation.id}/evidence`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            Explore trace graph <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>

        {/* Card 6: Standardized Report */}
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-topline">
            <span className="eyebrow">Stage 07</span>
            <FileCheck2 style={{ width: '16px', color: 'var(--lime)' }} />
          </div>
          <h3 style={{ margin: '14px 0 6px', fontSize: '18px', color: 'var(--warm)' }}>
            OIML R-76 Technical Report
          </h3>
          <p style={{ color: 'var(--muted)', fontSize: '12px', lineHeight: 1.5, margin: '0 0 20px' }}>
            Structured evaluation certificate ready for regulatory handoff and PDF export.
          </p>
          <Link href={`/evaluations/${evaluation.id}/report`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            Preview technical report <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>
      </div>
    </div>
  )
}
