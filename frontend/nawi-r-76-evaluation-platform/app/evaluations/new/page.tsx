'use client'

import React, { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  AlertCircle,
  ArrowRight,
  Check,
  ChevronDown,
  Gauge,
  Info,
  Layers,
  Plus,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { InstrumentRead, AccuracyClass, TareType } from '@/lib/types/domain'
import {
  getInstruments,
  createEvaluation,
  generateEvaluationPlan,
} from '@/lib/api/services'

function NewEvaluationForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialInstrumentId = searchParams.get('instrumentId')
  const initialConfigId = searchParams.get('configId')

  const [instruments, setInstruments] = useState<InstrumentRead[]>([])
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<string>(initialInstrumentId || '')
  const [selectedConfigId, setSelectedConfigId] = useState<string>(initialConfigId || '')
  const [loadingInstruments, setLoadingInstruments] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form states matching backend InstrumentConfiguration snapshot
  const [modelName, setModelName] = useState('ABC-300 Bench Scale')
  const [serialNumber, setSerialNumber] = useState('SYNTH-DEMO-NAWI-001-SN')
  const [manufacturer, setManufacturer] = useState('Global Bench Metrology Systems')
  const [accuracyClass, setAccuracyClass] = useState<AccuracyClass>('CLASS_III')
  const [maxCapacity, setMaxCapacity] = useState('30.000')
  const [minCapacity, setMinCapacity] = useState('0.200')
  const [eInterval, setEInterval] = useState('0.010')
  const [dInterval, setDInterval] = useState('0.010')
  const [unit, setUnit] = useState('kg')
  const [isMultipleRange, setIsMultipleRange] = useState(false)
  const [hasTare, setHasTare] = useState(true)
  const [hasZero, setHasZero] = useState(true)
  const [supportCount, setSupportCount] = useState<number>(4)
  const [labName, setLabName] = useState('National Metrology Institute — Legal Verification Lab')
  const [ruleVersion, setRuleVersion] = useState('2006-01')

  useEffect(() => {
    async function load() {
      setLoadingInstruments(true)
      const list = await getInstruments()
      setInstruments(list)
      if (list.length > 0) {
        const preselected = initialInstrumentId
          ? list.find((i) => i.id === initialInstrumentId) || list[0]
          : list[0]
        applyInstrument(preselected, initialConfigId || undefined)
      }
      setLoadingInstruments(false)
    }
    load()
  }, [initialInstrumentId, initialConfigId])

  function applyInstrument(inst: InstrumentRead, targetConfigId?: string) {
    setSelectedInstrumentId(inst.id)
    setModelName(inst.model_name)
    setSerialNumber(inst.serial_number)
    setManufacturer(inst.manufacturer)

    const cfg = targetConfigId
      ? inst.configurations?.find((c) => c.id === targetConfigId) || inst.configurations?.[0]
      : inst.configurations?.[0]

    if (cfg) {
      setSelectedConfigId(cfg.id)
      setAccuracyClass(cfg.accuracy_class)
      setMaxCapacity(String(cfg.max_capacity))
      setMinCapacity(String(cfg.min_capacity))
      setEInterval(String(cfg.verification_scale_interval))
      setDInterval(String(cfg.actual_scale_interval))
      setUnit(cfg.unit || 'kg')
      setIsMultipleRange(cfg.is_multiple_range)
      setHasTare(cfg.tare_type !== 'NONE')
      setHasZero(cfg.has_zero_setting)
      const sc = cfg.extra_capabilities?.load_receptor?.support_count
      if (sc) setSupportCount(sc)
    }
  }

  const handleInstrumentSelect = (id: string) => {
    const found = instruments.find((i) => i.id === id)
    if (found) {
      applyInstrument(found)
    }
  }

  const handleConfigSelect = (cfgId: string) => {
    const inst = instruments.find((i) => i.id === selectedInstrumentId)
    if (inst) {
      applyInstrument(inst, cfgId)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      // 1. Initialize Evaluation & Freeze Immutable Snapshot
      const evaluation = await createEvaluation(selectedInstrumentId || 'inst-001', {
        instrument_configuration_id: selectedConfigId || undefined,
        lab_name: labName,
        rule_version_id: ruleVersion,
      })

      // 2. Generate Plan deterministically from the snapshot
      await generateEvaluationPlan(evaluation.id)

      // 3. Navigate to the evaluation configuration overview
      router.push(`/evaluations/${evaluation.id}/configuration`)
    } catch (err: any) {
      console.error('Evaluation creation error:', err)
      setError(err.message || 'Failed to initialize evaluation.')
      setSubmitting(false)
    }
  }

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      {/* 01-07 Pipeline Stepper */}
      <Pipeline current={0} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>01</span>Instrument Specification & Evaluation Launch
          </div>
          <h1>Initialize Type Evaluation</h1>
          <p>
            Select a registered instrument from the catalog. The metrological specification below determines
            OIML R 76 test applicability and will be permanently captured as an immutable configuration snapshot.
          </p>
        </div>
      </div>

      {error && (
        <div
          className="panel"
          style={{
            padding: '16px 20px',
            marginBottom: '24px',
            background: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <AlertCircle style={{ width: '18px', flexShrink: 0 }} />
          <span style={{ fontSize: '12px' }}>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="config-layout">
          {/* Main Form Fields */}
          <div className="panel config-form">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Instrument Selection</span>
                <h2>Choose Registered NAWI</h2>
              </div>
              <Link href="/instruments/new" className="button button-outline" style={{ fontSize: '11px' }}>
                <Plus style={{ width: '12px' }} /> Register new instrument
              </Link>
            </div>

            {/* Instrument Selector Dropdown */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--dim)', marginBottom: '6px' }}>
                Registered Instrument
              </label>
              <select
                value={selectedInstrumentId}
                onChange={(e) => handleInstrumentSelect(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0d110f',
                  border: '1px solid var(--line)',
                  borderRadius: '6px',
                  color: 'var(--ink)',
                  fontSize: '12px',
                  padding: '10px 14px',
                  outline: 0,
                }}
              >
                {instruments.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.model_name} (SN: {i.serial_number}) — {i.manufacturer}
                  </option>
                ))}
              </select>
            </div>

            {/* Version picker if multiple configs exist */}
            {(() => {
              const currentInst = instruments.find((i) => i.id === selectedInstrumentId)
              if (currentInst && currentInst.configurations && currentInst.configurations.length > 1) {
                return (
                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '11px', color: 'var(--lime)', marginBottom: '6px', fontWeight: 600 }}>
                      Select Metrological Configuration Version
                    </label>
                    <select
                      value={selectedConfigId}
                      onChange={(e) => handleConfigSelect(e.target.value)}
                      style={{
                        width: '100%',
                        background: '#0d110f',
                        border: '1px solid #536b32',
                        borderRadius: '6px',
                        color: 'var(--ink)',
                        fontSize: '12px',
                        padding: '10px 14px',
                        outline: 0,
                      }}
                    >
                      {currentInst.configurations.map((cfg) => (
                        <option key={cfg.id} value={cfg.id}>
                          Configuration #{cfg.id.slice(0, 8)}: Max {cfg.max_capacity} {cfg.unit}, e={cfg.verification_scale_interval} {cfg.unit} ({cfg.is_multiple_range ? 'Multiple Range' : 'Single Range'})
                        </option>
                      ))}
                    </select>
                  </div>
                )
              }
              return null
            })()}

            <div className="field-grid">
              <label>
                Manufacturer
                <input value={manufacturer} readOnly />
              </label>
              <label>
                Model Name / Designation
                <input
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. ABC-300 Bench Scale"
                  required
                />
              </label>
              <label>
                Serial / Prototype Identifier
                <input
                  value={serialNumber}
                  onChange={(e) => setSerialNumber(e.target.value)}
                  placeholder="e.g. SN-2026-001"
                  required
                />
              </label>
              <label>
                Testing Laboratory
                <input
                  value={labName}
                  onChange={(e) => setLabName(e.target.value)}
                  placeholder="e.g. Legal Metrology Laboratory"
                  required
                />
              </label>
            </div>

            <div className="config-divider" />

            <div className="eyebrow" style={{ marginBottom: '16px' }}>
              Metrological Characteristics (R-76 Table 3 & 4)
            </div>

            <div className="field-grid">
              <label>
                Accuracy Class
                <select
                  value={accuracyClass}
                  onChange={(e) => setAccuracyClass(e.target.value as any)}
                >
                  <option value="CLASS_I">Class I — Special Accuracy</option>
                  <option value="CLASS_II">Class II — High Accuracy</option>
                  <option value="CLASS_III">Class III — Medium Accuracy</option>
                  <option value="CLASS_IIII">Class IIII — Ordinary Accuracy</option>
                </select>
              </label>
              <label>
                Base Mass Unit
                <select value={unit} onChange={(e) => setUnit(e.target.value)}>
                  <option value="kg">Kilograms (kg)</option>
                  <option value="g">Grams (g)</option>
                  <option value="mg">Milligrams (mg)</option>
                </select>
              </label>
              <label>
                Maximum Capacity (Max)
                <input
                  value={maxCapacity}
                  onChange={(e) => setMaxCapacity(e.target.value)}
                  required
                />
              </label>
              <label>
                Minimum Capacity (Min)
                <input
                  value={minCapacity}
                  onChange={(e) => setMinCapacity(e.target.value)}
                  required
                />
              </label>
              <label>
                Verification Scale Interval (e)
                <input
                  value={eInterval}
                  onChange={(e) => setEInterval(e.target.value)}
                  required
                />
              </label>
              <label>
                Actual Scale Interval (d)
                <input
                  value={dInterval}
                  onChange={(e) => setDInterval(e.target.value)}
                  required
                />
              </label>
            </div>

            <div className="config-divider" />

            <div className="eyebrow" style={{ marginBottom: '16px' }}>
              Receptor Geometry & Functional Facilities
            </div>

            <div className="choice-row">
              <div>
                <strong>Multiple Range Capability</strong>
                <span>Derives range-specific verification tests under clause A.4.4.4.</span>
              </div>
              <div className="segmented">
                <button
                  type="button"
                  className={!isMultipleRange ? 'selected' : ''}
                  onClick={() => setIsMultipleRange(false)}
                >
                  Off
                </button>
                <button
                  type="button"
                  className={isMultipleRange ? 'selected' : ''}
                  onClick={() => setIsMultipleRange(true)}
                >
                  On
                </button>
              </div>
            </div>

            <div className="choice-row">
              <div>
                <strong>Load Receptor Supports (N)</strong>
                <span>Controls A.4.7 eccentricity procedure (N ≤ 4 uses 4 quarter-segments; N &gt; 4 uses support points).</span>
              </div>
              <div className="segmented">
                <button
                  type="button"
                  className={supportCount === 4 ? 'selected' : ''}
                  onClick={() => setSupportCount(4)}
                >
                  N = 4 Points
                </button>
                <button
                  type="button"
                  className={supportCount === 6 ? 'selected' : ''}
                  onClick={() => setSupportCount(6)}
                >
                  N = 6 Points
                </button>
              </div>
            </div>

            <div className="choice-row">
              <div>
                <strong>Subtractive Tare Balancing Mechanism</strong>
                <span>Activates Tare Balancing & Weighing test (Clause A.4.6).</span>
              </div>
              <button
                type="button"
                className={`toggle ${hasTare ? 'on' : ''}`}
                onClick={() => setHasTare(!hasTare)}
                aria-label="Toggle tare mechanism"
              >
                <i aria-hidden="true" />
              </button>
            </div>

            <div className="choice-row">
              <div>
                <strong>Zero-Setting & Tracking Device</strong>
                <span>Activates Zero-Setting Range and Accuracy test (Clause A.4.2).</span>
              </div>
              <button
                type="button"
                className={`toggle ${hasZero ? 'on' : ''}`}
                onClick={() => setHasZero(!hasZero)}
                aria-label="Toggle zero setting"
              >
                <i aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Right Column: Pre-Flight Snapshot Preview */}
          <aside className="panel impact-panel" style={{ alignSelf: 'start' }}>
            <div className="impact-header">
              <div>
                <span className="eyebrow lime-text">Snapshot Pre-Flight</span>
                <h2>Immutable Evaluation Snapshot</h2>
              </div>
              <span className="engine-mark" aria-hidden="true">
                <ShieldCheck />
              </span>
            </div>

            <p style={{ color: 'var(--muted)', fontSize: '11px', lineHeight: 1.5, margin: '10px 0 20px' }}>
              When initialized, this configuration is captured with a cryptographic timestamp.
              Subsequent changes in the instrument registry will never overwrite this evaluation.
            </p>

            <div className="ready-stat">
              <span>Selected Standard</span>
              <strong>OIML R 76-1:2006 (E)</strong>
            </div>
            <div className="ready-stat">
              <span>Accuracy Class</span>
              <strong>{accuracyClass.replace('_', ' ')}</strong>
            </div>
            <div className="ready-stat">
              <span>Weighing Capacity</span>
              <strong>{maxCapacity} {unit}</strong>
            </div>
            <div className="ready-stat">
              <span>Verification Scale Interval</span>
              <strong>e = {eInterval} {unit}</strong>
            </div>
            <div className="ready-stat">
              <span>Eccentricity Procedure</span>
              <strong>{supportCount <= 4 ? 'A.4.7.1 (4 Quarters)' : 'A.4.7.2 (N Supports)'}</strong>
            </div>
            <div className="ready-stat">
              <span>Expected Procedures</span>
              <strong style={{ color: 'var(--lime)' }}>
                {isMultipleRange ? '10 procedures (+2 partial ranges)' : '09 procedures'}
              </strong>
            </div>

            <div className="config-divider" />

            <button
              type="submit"
              className="button"
              disabled={submitting}
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '14px',
                fontSize: '12px',
                opacity: submitting ? 0.7 : 1,
              }}
            >
              {submitting ? 'Freezing Snapshot & Generating Plan...' : 'Initialize evaluation & freeze snapshot'}{' '}
              <ArrowRight style={{ width: '13px' }} />
            </button>
          </aside>
        </div>
      </form>
    </div>
  )
}

export default function NewEvaluationPage() {
  return (
    <Suspense
      fallback={
        <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '60px 42px', textAlign: 'center' }}>
          <RefreshCw className="animate-spin" style={{ width: '24px', margin: '0 auto 12px', color: 'var(--lime)' }} />
          <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Loading evaluation form...</p>
        </div>
      }
    >
      <NewEvaluationForm />
    </Suspense>
  )
}
