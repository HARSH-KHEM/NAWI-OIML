'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowLeft,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Gauge,
  History,
  Layers,
  Lock,
  Plus,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { InstrumentRead, InstrumentConfigurationRead } from '@/lib/types/domain'
import { getInstrument } from '@/lib/api/services'

export default function InstrumentDetailPage() {
  const params = useParams()
  const instrumentId = (params?.id as string) || ''
  const [instrument, setInstrument] = useState<InstrumentRead | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      const data = await getInstrument(instrumentId)
      setInstrument(data)
      setLoading(false)
    }
    if (instrumentId) {
      load()
    }
  }, [instrumentId])

  if (loading) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '60px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '24px', margin: '0 auto 12px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Loading instrument details...</p>
      </div>
    )
  }

  if (!instrument) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '60px 42px', textAlign: 'center' }}>
        <h2>Instrument Not Found</h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', margin: '12px 0 20px' }}>
          No instrument identity exists with identifier: {instrumentId}
        </p>
        <Link href="/instruments" className="button" style={{ display: 'inline-flex' }}>
          <ArrowLeft style={{ width: '13px' }} /> Return to Catalog
        </Link>
      </div>
    )
  }

  const activeConfig = instrument.configurations?.[0]
  const isMulti = activeConfig?.is_multiple_range ?? false
  const supportCount = activeConfig?.extra_capabilities?.load_receptor?.support_count ?? 4

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>02</span>Instrument Record
          </div>
          <h1>{instrument.model_name}</h1>
          <p>
            {instrument.manufacturer} · Family: {instrument.instrument_family} · Serial:{' '}
            <span style={{ fontFamily: 'ui-monospace, monospace' }}>{instrument.serial_number}</span>
          </p>
        </div>
        <div className="header-actions">
          <Link href="/instruments" className="button button-outline">
            <ArrowLeft style={{ width: '13px' }} /> Catalog
          </Link>
          <Link href={`/evaluations/new?instrumentId=${instrument.id}`} className="button">
            Launch evaluation <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>
      </div>

      {/* Main Strip */}
      <div className="instrument-strip">
        <div className="instrument-symbol" aria-hidden="true">
          <Gauge />
        </div>
        <div>
          <span className="eyebrow">Metrological Identity</span>
          <h2>
            {instrument.model_name} <Badge tone={instrument.is_synthetic ? 'neutral' : 'lime'}>{instrument.status}</Badge>
          </h2>
          <p>Registered: {new Date(instrument.created_at).toLocaleDateString()} · Family: {instrument.instrument_family}</p>
        </div>
        {activeConfig && (
          <>
            <div className="strip-spec">
              <span>Max Capacity</span>
              <strong>{activeConfig.max_capacity} {activeConfig.unit}</strong>
            </div>
            <div className="strip-spec">
              <span>Scale Interval (e)</span>
              <strong>{activeConfig.verification_scale_interval} {activeConfig.unit}</strong>
            </div>
            <div className="strip-spec">
              <span>Accuracy Class</span>
              <strong>{activeConfig.accuracy_class.replace('_', ' ')}</strong>
            </div>
          </>
        )}
      </div>

      <div className="config-layout">
        {/* Left Column: Active Specification & Configuration Details */}
        <div className="panel config-form">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Active Configuration</span>
              <h2>Metrological Parameters (OIML R 76 Table 3)</h2>
            </div>
            <Badge tone="lime">Version Locked</Badge>
          </div>

          {activeConfig ? (
            <>
              <div className="field-grid">
                <label>
                  Manufacturer
                  <input value={instrument.manufacturer} readOnly />
                </label>
                <label>
                  Model Name
                  <input value={instrument.model_name} readOnly />
                </label>
                <label>
                  Serial Number
                  <input value={instrument.serial_number} readOnly />
                </label>
                <label>
                  Accuracy Class
                  <input value={activeConfig.accuracy_class.replace('_', ' ')} readOnly />
                </label>
                <label>
                  Maximum Capacity (Max)
                  <input value={`${activeConfig.max_capacity} ${activeConfig.unit}`} readOnly />
                </label>
                <label>
                  Minimum Capacity (Min)
                  <input value={`${activeConfig.min_capacity} ${activeConfig.unit}`} readOnly />
                </label>
                <label>
                  Verification Scale Interval (e)
                  <input value={`${activeConfig.verification_scale_interval} ${activeConfig.unit}`} readOnly />
                </label>
                <label>
                  Actual Scale Interval (d)
                  <input value={`${activeConfig.actual_scale_interval} ${activeConfig.unit}`} readOnly />
                </label>
              </div>

              <div className="config-divider" />

              <div className="eyebrow" style={{ marginBottom: '14px' }}>
                Receptor Geometry & Functional Facilities
              </div>

              <div className="choice-row">
                <div>
                  <strong>Range Architecture</strong>
                  <span>{isMulti ? 'Multiple range instrument with partial weighing ranges' : 'Single continuous weighing range'}</span>
                </div>
                <Badge tone={isMulti ? 'lime' : 'neutral'}>
                  {isMulti ? 'MULTIPLE RANGE' : 'SINGLE RANGE'}
                </Badge>
              </div>

              {isMulti && activeConfig.ranges && activeConfig.ranges.length > 0 && (
                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)', marginBottom: '16px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--lime)', fontWeight: 600, marginBottom: '10px' }}>
                    Configured Partial Weighing Ranges (Clause A.4.4.4):
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', fontSize: '11px' }}>
                    {activeConfig.ranges.map((r) => (
                      <div key={r.range_index} style={{ padding: '10px', background: '#121714', borderRadius: '6px' }}>
                        <strong style={{ color: 'var(--warm)', display: 'block', marginBottom: '4px' }}>
                          Range {r.range_index}
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
                  <strong>Tare Facility</strong>
                  <span>{activeConfig.tare_type} tare mechanism configured</span>
                </div>
                <Badge tone="lime">{activeConfig.tare_type}</Badge>
              </div>

              <div className="choice-row">
                <div>
                  <strong>Zero-Setting & Tracking Device</strong>
                  <span>{activeConfig.has_zero_setting ? 'Automatic/semi-automatic zero device active' : 'No zero-tracking device'}</span>
                </div>
                <Badge tone={activeConfig.has_zero_setting ? 'lime' : 'neutral'}>
                  {activeConfig.has_zero_setting ? 'ACTIVE' : 'INACTIVE'}
                </Badge>
              </div>

              <div className="choice-row">
                <div>
                  <strong>Load Receptor Support Points</strong>
                  <span>{supportCount} points (governs Clause A.4.7 eccentricity layout)</span>
                </div>
                <Badge tone="lime">N = {supportCount} POINTS</Badge>
              </div>
            </>
          ) : (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--muted)' }}>
              No configuration attached.
            </div>
          )}

          {/* Configuration History Section */}
          <div className="config-divider" />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History style={{ width: '15px', color: 'var(--lime)' }} />
              <span className="eyebrow" style={{ margin: 0 }}>Configuration Audit Trail</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
              {instrument.configurations?.length || 0} version(s) recorded
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(instrument.configurations || []).map((cfg, idx) => (
              <div
                key={cfg.id}
                style={{
                  padding: '12px 16px',
                  background: idx === 0 ? 'rgba(182, 237, 78, 0.04)' : '#0b0e0c',
                  border: `1px solid ${idx === 0 ? 'rgba(182, 237, 78, 0.2)' : 'var(--line)'}`,
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                    <strong style={{ color: idx === 0 ? 'var(--lime)' : 'var(--ink)' }}>
                      Configuration #{cfg.id.slice(0, 8)}
                    </strong>
                    {idx === 0 && <Badge tone="lime">Active</Badge>}
                  </div>
                  <span style={{ color: 'var(--dim)' }}>
                    Max: {cfg.max_capacity} {cfg.unit} · e: {cfg.verification_scale_interval} {cfg.unit} ·{' '}
                    {cfg.accuracy_class} · {cfg.is_multiple_range ? 'Multi-Range' : 'Single Range'}
                  </span>
                </div>
                <div style={{ textAlign: 'right', color: 'var(--dim)', fontSize: '10px' }}>
                  <Clock style={{ width: '11px', display: 'inline', marginRight: '4px' }} />
                  {new Date(cfg.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Pre-Flight Action Card */}
        <aside className="panel impact-panel" style={{ alignSelf: 'start' }}>
          <div className="impact-header">
            <div>
              <span className="eyebrow lime-text">Type Evaluation</span>
              <h2>Launch Evaluation</h2>
            </div>
            <span className="engine-mark" aria-hidden="true">
              <ShieldCheck />
            </span>
          </div>

          <p style={{ color: 'var(--muted)', fontSize: '11px', lineHeight: 1.5, margin: '10px 0 20px' }}>
            Initialize an authoritative OIML R 76 evaluation using this instrument. The active configuration will be
            captured as an immutable snapshot.
          </p>

          <div className="ready-stat">
            <span>Standard</span>
            <strong>OIML R 76-1:2006</strong>
          </div>
          <div className="ready-stat">
            <span>Primary Test</span>
            <strong>{isMulti ? 'A.4.4.4 (Partial Ranges)' : 'A.4.4 (Single Range)'}</strong>
          </div>
          <div className="ready-stat">
            <span>Eccentricity</span>
            <strong>{supportCount <= 4 ? 'A.4.7.1 (4 Quarters)' : 'A.4.7.2 (Supports)'}</strong>
          </div>
          <div className="ready-stat">
            <span>Repeatability</span>
            <strong>A.4.10 (Series A & B)</strong>
          </div>

          <div className="config-divider" />

          <Link
            href={`/evaluations/new?instrumentId=${instrument.id}`}
            className="button"
            style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '12px' }}
          >
            Launch evaluation with this instrument <ArrowRight style={{ width: '13px' }} />
          </Link>

          <p style={{ color: 'var(--dim)', fontSize: '10px', marginTop: '12px', textAlign: 'center' }}>
            Captures immutable snapshot · Preserves audit integrity
          </p>
        </aside>
      </div>
    </div>
  )
}
