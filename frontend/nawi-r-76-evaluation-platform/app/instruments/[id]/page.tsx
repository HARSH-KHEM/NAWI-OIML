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
import { InstrumentRead, InstrumentConfigurationRead, AccuracyClass, TareType } from '@/lib/types/domain'
import { getInstrument, createInstrumentConfiguration } from '@/lib/api/services'
import { formatDateSafe } from '@/lib/utils'

export default function InstrumentDetailPage() {
  const params = useParams()
  const instrumentId = (params?.id as string) || ''
  const [instrument, setInstrument] = useState<InstrumentRead | null>(null)
  const [loading, setLoading] = useState(true)

  // New configuration version form states
  const [showAddConfig, setShowAddConfig] = useState(false)
  const [savingConfig, setSavingConfig] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)
  const [cfgClass, setCfgClass] = useState<AccuracyClass>('CLASS_III')
  const [cfgMax, setCfgMax] = useState('30.000')
  const [cfgMin, setCfgMin] = useState('0.200')
  const [cfgE, setCfgE] = useState('0.010')
  const [cfgD, setCfgD] = useState('0.010')
  const [cfgUnit, setCfgUnit] = useState('kg')
  const [cfgIsMulti, setCfgIsMulti] = useState(false)
  const [cfgTare, setCfgTare] = useState<TareType>('SUBTRACTIVE')
  const [cfgZero, setCfgZero] = useState(true)
  const [cfgSupports, setCfgSupports] = useState(4)

  // Multi-range partial ranges
  const [r1Max, setR1Max] = useState('15.000')
  const [r1Min, setR1Min] = useState('0.100')
  const [r1E, setR1E] = useState('0.005')
  const [r1D, setR1D] = useState('0.005')
  const [r2Max, setR2Max] = useState('30.000')
  const [r2Min, setR2Min] = useState('0.200')
  const [r2E, setR2E] = useState('0.010')
  const [r2D, setR2D] = useState('0.010')

  async function reload() {
    if (!instrumentId) return
    const data = await getInstrument(instrumentId)
    setInstrument(data)
  }

  useEffect(() => {
    async function load() {
      setLoading(true)
      await reload()
      setLoading(false)
    }
    if (instrumentId) {
      load()
    }
  }, [instrumentId])

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault()
    setSavingConfig(true)
    setConfigError(null)

    try {
      const ranges = cfgIsMulti
        ? [
            {
              range_index: 1,
              min_capacity: r1Min,
              max_capacity: r1Max,
              verification_scale_interval: r1E,
              actual_scale_interval: r1D,
              unit: cfgUnit,
            },
            {
              range_index: 2,
              min_capacity: r2Min,
              max_capacity: r2Max,
              verification_scale_interval: r2E,
              actual_scale_interval: r2D,
              unit: cfgUnit,
            },
          ]
        : undefined

      await createInstrumentConfiguration(instrumentId, {
        accuracy_class: cfgClass,
        max_capacity: cfgMax,
        min_capacity: cfgMin,
        verification_scale_interval: cfgE,
        actual_scale_interval: cfgD,
        unit: cfgUnit,
        number_of_ranges: cfgIsMulti ? 2 : 1,
        is_multiple_range: cfgIsMulti,
        tare_type: cfgTare,
        is_electronic: true,
        has_zero_setting: cfgZero,
        extra_capabilities: {
          load_receptor: {
            support_count: cfgSupports,
            special_receptor: false,
            rolling_load: false,
          },
        },
        ranges,
      })

      await reload()
      setShowAddConfig(false)
    } catch (err: any) {
      console.error('Failed to create configuration:', err)
      setConfigError(err?.data?.detail || err.message || 'Failed to persist configuration')
    } finally {
      setSavingConfig(false)
    }
  }

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
          <p>Registered: {formatDateSafe(instrument.created_at)} · Family: {instrument.instrument_family}</p>
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

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History style={{ width: '15px', color: 'var(--lime)' }} />
              <span className="eyebrow" style={{ margin: 0 }}>Configuration Audit Trail</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                {instrument.configurations?.length || 0} version(s) recorded
              </span>
              <button
                type="button"
                className="button button-outline"
                onClick={() => setShowAddConfig(!showAddConfig)}
                style={{ fontSize: '11px', padding: '6px 12px' }}
              >
                <Plus style={{ width: '12px' }} /> {showAddConfig ? 'Cancel' : 'New Configuration Version'}
              </button>
            </div>
          </div>

          {/* New Configuration Form */}
          {showAddConfig && (
            <form
              onSubmit={handleSaveConfig}
              style={{
                background: '#0d120f',
                border: '1px solid #536b32',
                borderRadius: '8px',
                padding: '18px 20px',
                marginBottom: '20px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span className="eyebrow lime-text" style={{ margin: 0 }}>
                  Create New Metrological Configuration
                </span>
                <span style={{ fontSize: '10px', color: 'var(--dim)' }}>Will become new active version</span>
              </div>

              {configError && (
                <div style={{ color: '#f87171', fontSize: '11px', marginBottom: '12px' }}>
                  {configError}
                </div>
              )}

              <div className="field-grid" style={{ marginBottom: '14px' }}>
                <label>
                  Accuracy Class
                  <select value={cfgClass} onChange={(e) => setCfgClass(e.target.value as any)}>
                    <option value="CLASS_I">Class I</option>
                    <option value="CLASS_II">Class II</option>
                    <option value="CLASS_III">Class III</option>
                    <option value="CLASS_IIII">Class IIII</option>
                  </select>
                </label>
                <label>
                  Unit
                  <select value={cfgUnit} onChange={(e) => setCfgUnit(e.target.value)}>
                    <option value="kg">kg</option>
                    <option value="g">g</option>
                  </select>
                </label>
                <label>
                  Max Capacity
                  <input value={cfgMax} onChange={(e) => setCfgMax(e.target.value)} required />
                </label>
                <label>
                  Min Capacity
                  <input value={cfgMin} onChange={(e) => setCfgMin(e.target.value)} required />
                </label>
                <label>
                  Verification Interval (e)
                  <input value={cfgE} onChange={(e) => setCfgE(e.target.value)} required />
                </label>
                <label>
                  Actual Interval (d)
                  <input value={cfgD} onChange={(e) => setCfgD(e.target.value)} required />
                </label>
              </div>

              {/* Multiple Range Toggle */}
              <div className="choice-row" style={{ marginBottom: '14px' }}>
                <div>
                  <strong>Multiple Range Capability</strong>
                  <span style={{ fontSize: '11px', color: 'var(--dim)' }}>
                    Enable separate partial weighing ranges (Max₁, Max₂) under A.4.4.4.
                  </span>
                </div>
                <div className="segmented">
                  <button
                    type="button"
                    className={!cfgIsMulti ? 'selected' : ''}
                    onClick={() => setCfgIsMulti(false)}
                  >
                    Single Range
                  </button>
                  <button
                    type="button"
                    className={cfgIsMulti ? 'selected' : ''}
                    onClick={() => setCfgIsMulti(true)}
                  >
                    Multiple Range
                  </button>
                </div>
              </div>

              {cfgIsMulti && (
                <div style={{ background: '#121714', borderRadius: '6px', padding: '12px', marginBottom: '14px', border: '1px solid var(--line)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--lime)', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
                    Partial Weighing Ranges Setup (OIML A.4.4.4):
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                    <div>
                      <strong style={{ fontSize: '11px', color: 'var(--warm)' }}>Partial Range 1:</strong>
                      <div className="field-grid" style={{ marginTop: '6px' }}>
                        <label>Max₁ <input value={r1Max} onChange={(e) => setR1Max(e.target.value)} /></label>
                        <label>e₁ <input value={r1E} onChange={(e) => setR1E(e.target.value)} /></label>
                      </div>
                    </div>
                    <div>
                      <strong style={{ fontSize: '11px', color: 'var(--warm)' }}>Partial Range 2:</strong>
                      <div className="field-grid" style={{ marginTop: '6px' }}>
                        <label>Max₂ <input value={r2Max} onChange={(e) => setR2Max(e.target.value)} /></label>
                        <label>e₂ <input value={r2E} onChange={(e) => setR2E(e.target.value)} /></label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="button"
                disabled={savingConfig}
                style={{ width: '100%', justifyContent: 'center', fontSize: '11px', padding: '10px' }}
              >
                {savingConfig ? 'Persisting Configuration Version...' : 'Save & Persist Configuration Version'}
              </button>
            </form>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(instrument.configurations || []).map((cfg, idx) => (
              <div
                key={cfg.id}
                style={{
                  padding: '14px 16px',
                  background: idx === 0 ? 'rgba(182, 237, 78, 0.04)' : '#0b0e0c',
                  border: `1px solid ${idx === 0 ? 'rgba(182, 237, 78, 0.2)' : 'var(--line)'}`,
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  flexWrap: 'wrap',
                  fontSize: '11px',
                }}
              >
                <div style={{ flex: 1, minWidth: '220px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <strong style={{ color: idx === 0 ? 'var(--lime)' : 'var(--ink)' }}>
                      Configuration #{cfg.id.slice(0, 8)}
                    </strong>
                    {idx === 0 && <Badge tone="lime">Active</Badge>}
                    <Badge tone={cfg.is_multiple_range ? 'lime' : 'neutral'}>
                      {cfg.is_multiple_range ? 'Multi-Range' : 'Single Range'}
                    </Badge>
                  </div>
                  <span style={{ color: 'var(--dim)', display: 'block', fontSize: '11px' }}>
                    Max: {cfg.max_capacity} {cfg.unit} · e: {cfg.verification_scale_interval} {cfg.unit} ·{' '}
                    Class: {cfg.accuracy_class.replace('_', ' ')}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{ textAlign: 'right', color: 'var(--dim)', fontSize: '10px' }}>
                    <Clock style={{ width: '11px', display: 'inline', marginRight: '4px' }} />
                    {formatDateSafe(cfg.created_at)}
                  </div>
                  <Link
                    href={`/evaluations/new?instrumentId=${instrument.id}&configId=${cfg.id}`}
                    className="button button-secondary"
                    style={{ padding: '6px 12px', fontSize: '11px' }}
                    title="Launch new evaluation using this specific configuration snapshot"
                  >
                    Evaluate this version <ArrowRight style={{ width: '11px' }} />
                  </Link>
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
