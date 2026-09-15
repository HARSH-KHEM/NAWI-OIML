'use client'

import React from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowRight, Check, Gauge, Lock, ShieldCheck, SlidersHorizontal } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationConfigurationPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]
  const inst = evaluation.instrument

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={0} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>01</span>Configuration Snapshot
          </div>
          <h1>Instrument Specification</h1>
          <p>
            Immutable metrological specification captured at evaluation initialization.
            In legal metrology, configuration changes spawn new versioned snapshots rather than silently rewriting audit history.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button">
            Review applicable test plan <ArrowRight />
          </Link>
        </div>
      </div>

      {/* Snapshot Header Notice */}
      <div className="instrument-strip" style={{ borderColor: '#536b32' }}>
        <div className="instrument-symbol" aria-hidden="true">
          <Lock />
        </div>
        <div>
          <span className="eyebrow lime-text">Sealed Audit Record · Snapshot Active</span>
          <h2>
            {inst.modelName} <Badge tone="lime">Snapshot Frozen</Badge>
          </h2>
          <p>Captured on {new Date(evaluation.createdAt).toUTCString()} · Evaluator: {evaluation.operatorName}</p>
        </div>
        <div className="strip-spec">
          <span>Max Capacity</span>
          <strong>{inst.maxCapacity} {inst.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Verification Interval (e)</span>
          <strong>{inst.verificationScaleInterval} {inst.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Accuracy Class</span>
          <strong>{inst.accuracyClass.replace('_', ' ')}</strong>
        </div>
      </div>

      <div className="config-layout">
        {/* Left: Detailed Parameters */}
        <div className="panel config-form">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Metrological Specification</span>
              <h2>Parameters driving applicability</h2>
            </div>
            <span className="autosave">
              <Check style={{ width: '12px', display: 'inline', verticalAlign: '-1px' }} /> Verified
            </span>
          </div>

          <div className="field-grid">
            <label>
              Manufacturer
              <input value={inst.manufacturer} readOnly />
            </label>
            <label>
              Model Designation
              <input value={inst.modelName} readOnly />
            </label>
            <label>
              Serial Number
              <input value={inst.serialNumber} readOnly />
            </label>
            <label>
              Accuracy Class
              <input value={inst.accuracyClass.replace('_', ' ')} readOnly />
            </label>
            <label>
              Maximum Capacity (Max)
              <input value={`${inst.maxCapacity} ${inst.unit}`} readOnly />
            </label>
            <label>
              Minimum Capacity (Min)
              <input value={`${inst.minCapacity} ${inst.unit}`} readOnly />
            </label>
            <label>
              Verification Scale Interval (e)
              <input value={`${inst.verificationScaleInterval} ${inst.unit}`} readOnly />
            </label>
            <label>
              Actual Scale Interval (d)
              <input value={`${inst.actualScaleInterval} ${inst.unit}`} readOnly />
            </label>
          </div>

          <div className="config-divider" />

          <div className="eyebrow" style={{ marginBottom: '14px' }}>
            Functional & Geometric Capabilities
          </div>

          <div className="choice-row">
            <div>
              <strong>Multiple Range Capability</strong>
              <span>
                {inst.isMultipleRange
                  ? 'Active: 2 partial weighing ranges configured with separate scale intervals.'
                  : 'Inactive: Single continuous weighing range.'}
              </span>
            </div>
            <Badge tone={inst.isMultipleRange ? 'lime' : 'neutral'}>
              {inst.isMultipleRange ? 'MULTIPLE RANGE (2)' : 'SINGLE RANGE'}
            </Badge>
          </div>

          <div className="choice-row">
            <div>
              <strong>Tare Device Facility</strong>
              <span>Subtractive tare device enabled under OIML R 76-1:2006 clause A.4.6.</span>
            </div>
            <Badge tone="lime">SUBTRACTIVE TARE</Badge>
          </div>

          <div className="choice-row">
            <div>
              <strong>Zero-Setting & Tracking Mechanism</strong>
              <span>Automatic and semi-automatic zero-setting device under clause A.4.2.</span>
            </div>
            <Badge tone="lime">ZERO DEVICE ACTIVE</Badge>
          </div>

          <div className="choice-row">
            <div>
              <strong>Load Receptor Support Geometry</strong>
              <span>4 support points (clause A.4.7.1 four quarter-segments eccentricity procedure).</span>
            </div>
            <Badge tone="lime">4 SUPPORTS (QUARTERS)</Badge>
          </div>
        </div>

        {/* Right: Applicability Consequence Summary */}
        <aside className="panel impact-panel">
          <div className="impact-header">
            <div>
              <span className="eyebrow lime-text">Applicability Summary</span>
              <h2>Plan consequences</h2>
            </div>
            <span className="engine-mark" aria-hidden="true">
              <ShieldCheck />
            </span>
          </div>

          <div className="impact-count">
            <strong>09</strong>
            <div>
              <span>applicable procedures</span>
              <small>All Table 6 criteria locked to this snapshot</small>
            </div>
          </div>

          <div className="ready-stat">
            <span>Standard Version</span>
            <strong>{evaluation.ruleVersion}</strong>
          </div>
          <div className="ready-stat">
            <span>Primary Test</span>
            <strong>Weighing Performance (A.4.4)</strong>
          </div>
          <div className="ready-stat">
            <span>Eccentricity Mode</span>
            <strong>4 Quarter-Segments (A.4.7.1)</strong>
          </div>
          <div className="ready-stat">
            <span>Repeatability Mode</span>
            <strong>Dual-Series A & B (A.4.10)</strong>
          </div>

          <div className="config-divider" />

          <p style={{ color: 'var(--muted)', fontSize: '11px', lineHeight: 1.5 }}>
            Any subsequent changes in the master instrument catalogue will not alter this evaluation.
            Audit traceability is strictly preserved.
          </p>

          <Link
            href={`/evaluations/${evaluation.id}/plan`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', marginTop: '16px' }}
          >
            Go to generated test plan <ArrowRight />
          </Link>
        </aside>
      </div>
    </div>
  )
}
