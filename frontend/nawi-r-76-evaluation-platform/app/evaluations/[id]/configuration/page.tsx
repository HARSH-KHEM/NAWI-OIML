'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  Clock,
  Gauge,
  Layers,
  Lock,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { EvaluationRead } from '@/lib/types/domain'
import { getEvaluation } from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationConfigurationPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      const data = await getEvaluation(evaluationId)
      if (data) {
        setEvaluation(data)
      } else {
        // Fallback to mock evaluation
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
            extra_capabilities: {
              load_receptor: {
                support_count: mock.instrument.loadReceptor.supportCount,
                special_receptor: mock.instrument.loadReceptor.specialReceptor,
                rolling_load: mock.instrument.loadReceptor.rollingLoad,
              },
            },
            ranges: mock.instrument.isMultipleRange
              ? [
                  {
                    range_index: 1,
                    min_capacity: '0.100',
                    max_capacity: '15.000',
                    verification_scale_interval: '0.005',
                    actual_scale_interval: '0.005',
                    unit: mock.instrument.unit,
                  },
                  {
                    range_index: 2,
                    min_capacity: '0.200',
                    max_capacity: '30.000',
                    verification_scale_interval: '0.010',
                    actual_scale_interval: '0.010',
                    unit: mock.instrument.unit,
                  },
                ]
              : [],
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
      setLoading(false)
    }
    load()
  }, [evaluationId])

  if (loading || !evaluation) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '60px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '24px', margin: '0 auto 12px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Loading configuration snapshot...</p>
      </div>
    )
  }

  const snap = evaluation.configuration_snapshot
  const isMulti = snap.is_multiple_range
  const supportCount = snap.extra_capabilities?.load_receptor?.support_count ?? 4
  const ranges = snap.ranges || []

  // Deterministic procedure count calculation
  const totalProcedures = isMulti ? 10 : 9
  const applicableProcedures = isMulti ? 6 : 4

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={0} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>01</span>Configuration Snapshot · Evaluation #{evaluation.evaluation_number}
          </div>
          <h1>Instrument Specification & Snapshot</h1>
          <p>
            Immutable metrological specification captured at evaluation initialization.
            In legal metrology, configuration changes spawn new versioned snapshots rather than silently rewriting audit history.
          </p>
        </div>
        <div className="header-actions">
          <Link href={`/evaluations/${evaluation.id}/plan`} className="button">
            Review applicable test plan <ArrowRight style={{ width: '13px' }} />
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
            {snap.model_name} <Badge tone="lime">Snapshot Frozen</Badge>
          </h2>
          <p>
            Captured on {new Date(snap.snapshot_timestamp || evaluation.created_at).toUTCString()} · Lab: {evaluation.lab_name || 'Legal Metrology Lab'}
          </p>
        </div>
        <div className="strip-spec">
          <span>Max Capacity</span>
          <strong>{snap.max_capacity} {snap.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Verification Interval (e)</span>
          <strong>{snap.verification_scale_interval} {snap.unit}</strong>
        </div>
        <div className="strip-spec">
          <span>Accuracy Class</span>
          <strong>{snap.accuracy_class.replace('_', ' ')}</strong>
        </div>
      </div>

      <div className="config-layout">
        {/* Left: Detailed Parameters */}
        <div className="panel config-form">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Frozen Metrological Specification</span>
              <h2>Parameters driving applicability</h2>
            </div>
            <span className="autosave">
              <Check style={{ width: '12px', display: 'inline', verticalAlign: '-1px' }} /> Immutable Seal
            </span>
          </div>

          <div className="field-grid">
            <label>
              Manufacturer
              <input value={snap.manufacturer} readOnly />
            </label>
            <label>
              Model Designation
              <input value={snap.model_name} readOnly />
            </label>
            <label>
              Serial Number
              <input value={snap.instrument_serial} readOnly />
            </label>
            <label>
              Accuracy Class
              <input value={snap.accuracy_class.replace('_', ' ')} readOnly />
            </label>
            <label>
              Maximum Capacity (Max)
              <input value={`${snap.max_capacity} ${snap.unit}`} readOnly />
            </label>
            <label>
              Minimum Capacity (Min)
              <input value={`${snap.min_capacity} ${snap.unit}`} readOnly />
            </label>
            <label>
              Verification Scale Interval (e)
              <input value={`${snap.verification_scale_interval} ${snap.unit}`} readOnly />
            </label>
            <label>
              Actual Scale Interval (d)
              <input value={`${snap.actual_scale_interval} ${snap.unit}`} readOnly />
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
                {isMulti
                  ? 'Active: Multiple partial weighing ranges configured with separate scale intervals.'
                  : 'Inactive: Single continuous weighing range.'}
              </span>
            </div>
            <Badge tone={isMulti ? 'lime' : 'neutral'}>
              {isMulti ? `MULTIPLE RANGE (${ranges.length || 2} RANGES)` : 'SINGLE RANGE'}
            </Badge>
          </div>

          {/* If Multi-Range: Display each partial range */}
          {isMulti && ranges.length > 0 && (
            <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)', marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--lime)', fontWeight: 600, marginBottom: '10px' }}>
                Configured Partial Weighing Ranges (OIML R 76 Clause A.4.4.4):
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '11px' }}>
                {ranges.map((r) => (
                  <div key={r.range_index} style={{ padding: '10px 12px', background: '#121714', borderRadius: '6px' }}>
                    <strong style={{ color: 'var(--warm)', display: 'block', marginBottom: '4px' }}>
                      Partial Range {r.range_index} (W{r.range_index})
                    </strong>
                    <div style={{ color: 'var(--dim)', lineHeight: 1.6, fontFamily: 'ui-monospace, monospace' }}>
                      Min: {r.min_capacity} {r.unit}<br />
                      Max: {r.max_capacity} {r.unit}<br />
                      e: {r.verification_scale_interval} {r.unit} · d: {r.actual_scale_interval} {r.unit}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="choice-row">
            <div>
              <strong>Tare Device Facility</strong>
              <span>{snap.tare_type} tare device enabled under OIML R 76-1:2006 clause A.4.6.</span>
            </div>
            <Badge tone="lime">{snap.tare_type} TARE</Badge>
          </div>

          <div className="choice-row">
            <div>
              <strong>Zero-Setting & Tracking Mechanism</strong>
              <span>
                {snap.has_zero_setting
                  ? 'Automatic and semi-automatic zero-setting device under clause A.4.2.'
                  : 'Manual zero setting device.'}
              </span>
            </div>
            <Badge tone={snap.has_zero_setting ? 'lime' : 'neutral'}>
              {snap.has_zero_setting ? 'ZERO DEVICE ACTIVE' : 'MANUAL'}
            </Badge>
          </div>

          <div className="choice-row">
            <div>
              <strong>Load Receptor Support Geometry</strong>
              <span>
                {supportCount} support points (governs Clause A.4.7 eccentricity procedure:{' '}
                {supportCount <= 4 ? 'A.4.7.1 four quarter-segments' : 'A.4.7.2 support points'}).
              </span>
            </div>
            <Badge tone="lime">N = {supportCount} SUPPORTS</Badge>
          </div>
        </div>

        {/* Right: Applicability Consequence Summary */}
        <aside className="panel impact-panel" style={{ alignSelf: 'start' }}>
          <div className="impact-header">
            <div>
              <span className="eyebrow lime-text">Applicability Summary</span>
              <h2>Plan Consequences</h2>
            </div>
            <span className="engine-mark" aria-hidden="true">
              <ShieldCheck />
            </span>
          </div>

          <div className="impact-count">
            <strong>{String(applicableProcedures).padStart(2, '0')}</strong>
            <div>
              <span>applicable procedures</span>
              <small>All Table 6 criteria locked to this snapshot</small>
            </div>
          </div>

          <div className="ready-stat">
            <span>Standard Version</span>
            <strong>{evaluation.rule_version_id || 'OIML R 76-1:2006'}</strong>
          </div>
          <div className="ready-stat">
            <span>Primary Weighing</span>
            <strong>{isMulti ? 'A.4.4.4 (Range 1 & Range 2)' : 'A.4.4 (Single Range)'}</strong>
          </div>
          <div className="ready-stat">
            <span>Eccentricity Mode</span>
            <strong>{supportCount <= 4 ? 'A.4.7.1 (4 Quarter-Segments)' : 'A.4.7.2 (Support Points)'}</strong>
          </div>
          <div className="ready-stat">
            <span>Repeatability Mode</span>
            <strong>Dual-Series A & B (A.4.10)</strong>
          </div>
          <div className="ready-stat">
            <span>Tare Procedure</span>
            <strong>{snap.tare_type !== 'NONE' ? 'A.4.6 (Applicable)' : 'Not Applicable'}</strong>
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
            Go to generated test plan <ArrowRight style={{ width: '13px' }} />
          </Link>
        </aside>
      </div>
    </div>
  )
}
