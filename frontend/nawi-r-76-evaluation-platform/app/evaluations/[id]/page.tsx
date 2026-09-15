'use client'

import React from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  ClipboardCheck,
  FileCheck2,
  Gauge,
  GitBranch,
  Play,
  ShieldCheck,
  SlidersHorizontal,
  TestTube2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationDetailPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]

  const inst = evaluation.instrument

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      {/* 01-07 Pipeline Stepper */}
      <Pipeline current={1} evaluationId={evaluation.id} />

      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>{evaluation.evaluationNumber}</span>Type Evaluation Hub
          </div>
          <h1>{inst.modelName}</h1>
          <p>
            {inst.manufacturer} · Standard: {evaluation.ruleVersion} · Registered by {evaluation.operatorName}
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button">
            View generated test plan <ArrowRight />
          </Link>
        </div>
      </div>

      {/* Instrument Metrology Strip */}
      <div className="instrument-strip">
        <div className="instrument-symbol" aria-hidden="true">
          <Gauge />
        </div>
        <div>
          <span className="eyebrow">Frozen Snapshot / {inst.serialNumber}</span>
          <h2>
            {inst.modelName} <Badge tone={evaluation.status === 'COMPLIANT' ? 'lime' : 'amber'}>{evaluation.status}</Badge>
          </h2>
          <p>Non-automatic weighing instrument · {inst.accuracyClass.replace('_', ' ')}</p>
        </div>
        <div className="strip-spec">
          <span>Max Capacity</span>
          <strong>{inst.maxCapacity} {inst.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Min Capacity</span>
          <strong>{inst.minCapacity} {inst.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Scale Interval (e)</span>
          <strong>{inst.verificationScaleInterval} {inst.unit}</strong>
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
            Inspect configuration <ArrowRight />
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
            {evaluation.totalProcedures} rule-derived procedures scheduled based on instrument configuration.
          </p>
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button button-secondary" style={{ marginTop: 'auto' }}>
            Open test schedule <ArrowRight />
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
          <Link href={`/evaluations/${evaluation.id}/tests/test-wp-01`} className="button" style={{ marginTop: 'auto' }}>
            Enter test workspace <Play />
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
            View calculations <ArrowRight />
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
            Explore trace graph <ArrowRight />
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
            Preview technical report <ArrowRight />
          </Link>
        </div>
      </div>
    </div>
  )
}
