'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  Gauge,
  Info,
  Layers,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { AccuracyClass, TareType } from '@/lib/types/domain'
import { createInstrument, createInstrumentConfiguration } from '@/lib/api/services'

type Step = 1 | 2 | 3 | 4 | 5

export default function RegisterInstrumentPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<Step>(1)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Step 1: Instrument Identity
  const [manufacturer, setManufacturer] = useState('Global Bench Metrology Systems')
  const [modelName, setModelName] = useState('ABC-500 Heavy Industrial Scale')
  const [instrumentFamily, setInstrumentFamily] = useState('NAWI')
  const [serialNumber, setSerialNumber] = useState(`SN-${Math.floor(100000 + Math.random() * 900000)}`)
  const [isSynthetic, setIsSynthetic] = useState(false)

  // Step 2: Metrological Parameters
  const [accuracyClass, setAccuracyClass] = useState<AccuracyClass>('CLASS_III')
  const [unit, setUnit] = useState('kg')
  const [maxCapacity, setMaxCapacity] = useState('60.000')
  const [minCapacity, setMinCapacity] = useState('0.400')
  const [eInterval, setEInterval] = useState('0.020')
  const [dInterval, setDInterval] = useState('0.020')

  // Step 3: Functional & Receptor Capabilities
  const [isMultipleRange, setIsMultipleRange] = useState(false)
  const [tareType, setTareType] = useState<TareType>('SUBTRACTIVE')
  const [hasZeroSetting, setHasZeroSetting] = useState(true)
  const [isElectronic, setIsElectronic] = useState(true)
  const [supportCount, setSupportCount] = useState<number>(4)
  const [specialReceptor, setSpecialReceptor] = useState(false)
  const [rollingLoad, setRollingLoad] = useState(false)

  // Step 4: Multi-Range Parameters (if enabled)
  const [r1Min, setR1Min] = useState('0.200')
  const [r1Max, setR1Max] = useState('30.000')
  const [r1E, setR1E] = useState('0.010')
  const [r1D, setR1D] = useState('0.010')

  const [r2Min, setR2Min] = useState('0.400')
  const [r2Max, setR2Max] = useState('60.000')
  const [r2E, setR2E] = useState('0.020')
  const [r2D, setR2D] = useState('0.020')

  // Validation Logic (OIML R 76-1:2006)
  const numMax = parseFloat(maxCapacity) || 0
  const numMin = parseFloat(minCapacity) || 0
  const numE = parseFloat(eInterval) || 0
  const numD = parseFloat(dInterval) || 0

  const validationErrors: string[] = []
  if (!manufacturer.trim()) validationErrors.push('Manufacturer name is mandatory.')
  if (!modelName.trim()) validationErrors.push('Model designation is mandatory.')
  if (!serialNumber.trim()) validationErrors.push('Serial / Prototype identifier is mandatory.')

  if (numMax <= 0) validationErrors.push('Maximum capacity (Max) must be strictly greater than zero.')
  if (numMin <= 0) validationErrors.push('Minimum capacity (Min) must be strictly greater than zero.')
  if (numMin > numMax) validationErrors.push('Minimum capacity (Min) cannot exceed Maximum capacity (Max).')

  if (numE <= 0) validationErrors.push('Verification scale interval (e) must be strictly positive.')
  if (numD <= 0) validationErrors.push('Actual scale interval (d) must be strictly positive.')
  if (numD > numE) {
    validationErrors.push('Actual scale interval (d) cannot exceed verification scale interval (e) under OIML R 76 Clause 3.1.')
  }

  // Multi-range validation
  if (isMultipleRange) {
    const numR1Max = parseFloat(r1Max) || 0
    const numR2Max = parseFloat(r2Max) || 0
    const numR1E = parseFloat(r1E) || 0
    const numR2E = parseFloat(r2E) || 0

    if (numR1Max <= 0 || numR2Max <= 0) validationErrors.push('All partial range capacities must be strictly positive.')
    if (numR1Max >= numR2Max) validationErrors.push('Partial range 1 capacity (Max₁) must be strictly less than range 2 (Max₂).')
    if (numR1E > numR2E) validationErrors.push('Scale interval e₁ cannot exceed e₂ in multiple range instruments.')
  }

  // Number of verification scale intervals n = Max / e
  const scaleIntervalsCount = numE > 0 ? Math.round(numMax / numE) : 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (validationErrors.length > 0) return

    setSubmitting(true)
    setSubmitError(null)

    try {
      // 1. Create Instrument Identity
      const instrument = await createInstrument({
        manufacturer,
        model_name: modelName,
        instrument_family: instrumentFamily,
        serial_number: serialNumber,
        status: 'ACTIVE',
        is_synthetic: isSynthetic,
      })

      // 2. Create and attach Metrological Configuration
      const ranges = isMultipleRange
        ? [
            {
              range_index: 1,
              min_capacity: r1Min,
              max_capacity: r1Max,
              verification_scale_interval: r1E,
              actual_scale_interval: r1D,
              unit,
            },
            {
              range_index: 2,
              min_capacity: r2Min,
              max_capacity: r2Max,
              verification_scale_interval: r2E,
              actual_scale_interval: r2D,
              unit,
            },
          ]
        : []

      await createInstrumentConfiguration(instrument.id, {
        accuracy_class: accuracyClass,
        max_capacity: maxCapacity,
        min_capacity: minCapacity,
        verification_scale_interval: eInterval,
        actual_scale_interval: dInterval,
        unit,
        number_of_ranges: isMultipleRange ? 2 : 1,
        is_multiple_range: isMultipleRange,
        tare_type: tareType,
        is_electronic: isElectronic,
        has_zero_setting: hasZeroSetting,
        extra_capabilities: {
          load_receptor: {
            support_count: supportCount,
            special_receptor: specialReceptor,
            rolling_load: rollingLoad,
          },
        },
        ranges,
      })

      // Redirect to newly registered instrument details page
      router.push(`/instruments/${instrument.id}`)
    } catch (err: any) {
      console.error('Registration failed:', err)
      setSubmitError(err.message || 'Failed to complete instrument registration.')
      setSubmitting(false)
    }
  }

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>01</span>Registration Workflow
          </div>
          <h1>Register Weighing Instrument</h1>
          <p>
            Capture the legal metrology identity and initial configuration of a NAWI.
            Metrological rules validate mathematical hierarchy (Min ≤ Max, d ≤ e, n limits) before persistence.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/instruments" className="button button-outline">
            <ArrowLeft style={{ width: '13px' }} /> Return to Catalog
          </Link>
        </div>
      </div>

      {/* Multi-step progress navigation */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', overflowX: 'auto' }}>
          {[
            { step: 1, title: '1. Identity' },
            { step: 2, title: '2. Metrology' },
            { step: 3, title: '3. Capabilities' },
            ...(isMultipleRange ? [{ step: 4, title: '4. Multi-Range' }] : []),
            { step: 5, title: '5. Review & Seal' },
          ].map((item) => (
            <button
              key={item.step}
              type="button"
              onClick={() => setCurrentStep(item.step as Step)}
              style={{
                background: currentStep === item.step ? 'rgba(182, 237, 78, 0.12)' : 'transparent',
                border: currentStep === item.step ? '1px solid var(--lime)' : '1px solid transparent',
                borderRadius: '6px',
                padding: '8px 14px',
                color: currentStep === item.step ? 'var(--lime)' : 'var(--dim)',
                fontSize: '11px',
                fontFamily: 'ui-monospace, monospace',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap',
              }}
            >
              {currentStep > item.step ? (
                <Check style={{ width: '12px', color: 'var(--lime)' }} />
              ) : null}
              {item.title}
            </button>
          ))}
        </div>
      </div>

      {submitError && (
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
          <span style={{ fontSize: '12px' }}>{submitError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="config-layout">
          {/* Main Wizard Form Column */}
          <div className="panel config-form">
            {/* STEP 1: IDENTITY */}
            {currentStep === 1 && (
              <div>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Step 01 / Identity</span>
                    <h2>Instrument Physical & Type Identity</h2>
                  </div>
                  <Badge tone={isSynthetic ? 'neutral' : 'lime'}>
                    {isSynthetic ? 'Synthetic Fixture' : 'Physical Prototype'}
                  </Badge>
                </div>

                <div className="field-grid">
                  <label>
                    Manufacturer Name
                    <input
                      value={manufacturer}
                      onChange={(e) => setManufacturer(e.target.value)}
                      placeholder="e.g. Mettler Toledo or Sartorius"
                      required
                    />
                  </label>
                  <label>
                    Model Name / Designation
                    <input
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      placeholder="e.g. ABC-500 Heavy Bench Scale"
                      required
                    />
                  </label>
                  <label>
                    Instrument Family
                    <input
                      value={instrumentFamily}
                      onChange={(e) => setInstrumentFamily(e.target.value)}
                      placeholder="e.g. NAWI (Non-Automatic Weighing Instrument)"
                      required
                    />
                  </label>
                  <label>
                    Serial / Prototype Identifier
                    <input
                      value={serialNumber}
                      onChange={(e) => setSerialNumber(e.target.value)}
                      placeholder="e.g. SN-2026-908"
                      required
                    />
                  </label>
                </div>

                <div className="config-divider" />

                <div className="choice-row">
                  <div>
                    <strong>Synthetic Laboratory Demonstration Fixture</strong>
                    <span>Flag instrument as a synthetic benchmark test fixture rather than an active commercial prototype.</span>
                  </div>
                  <button
                    type="button"
                    className={`toggle ${isSynthetic ? 'on' : ''}`}
                    onClick={() => setIsSynthetic(!isSynthetic)}
                    aria-label="Toggle synthetic fixture"
                  >
                    <i aria-hidden="true" />
                  </button>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    className="button"
                    onClick={() => setCurrentStep(2)}
                  >
                    Next: Metrological Parameters <ArrowRight style={{ width: '13px' }} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: METROLOGICAL PARAMETERS */}
            {currentStep === 2 && (
              <div>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Step 02 / Metrology</span>
                    <h2>Metrological Characteristics (R-76 Table 3)</h2>
                  </div>
                  <Badge tone="lime">OIML R 76-1:2006</Badge>
                </div>

                <div className="field-grid">
                  <label>
                    Accuracy Class
                    <select
                      value={accuracyClass}
                      onChange={(e) => setAccuracyClass(e.target.value as AccuracyClass)}
                    >
                      <option value="CLASS_I">Class I — Special Accuracy</option>
                      <option value="CLASS_II">Class II — High Accuracy</option>
                      <option value="CLASS_III">Class III — Medium Accuracy</option>
                      <option value="CLASS_IIII">Class IIII — Ordinary Accuracy</option>
                    </select>
                  </label>
                  <label>
                    Base Metrological Unit
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
                      placeholder="e.g. 60.000"
                      required
                    />
                  </label>
                  <label>
                    Minimum Capacity (Min)
                    <input
                      value={minCapacity}
                      onChange={(e) => setMinCapacity(e.target.value)}
                      placeholder="e.g. 0.400"
                      required
                    />
                  </label>
                  <label>
                    Verification Scale Interval (e)
                    <input
                      value={eInterval}
                      onChange={(e) => setEInterval(e.target.value)}
                      placeholder="e.g. 0.020"
                      required
                    />
                  </label>
                  <label>
                    Actual Scale Interval (d)
                    <input
                      value={dInterval}
                      onChange={(e) => setDInterval(e.target.value)}
                      placeholder="e.g. 0.020"
                      required
                    />
                  </label>
                </div>

                <div className="config-divider" />

                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--lime)', fontWeight: 600, marginBottom: '8px' }}>
                    Calculated Metrological Verification:
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '11px' }}>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Resolution Count (n = Max/e):</span>
                      <strong style={{ fontFamily: 'ui-monospace, monospace', color: 'var(--ink)' }}>
                        {scaleIntervalsCount.toLocaleString()} intervals
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>d ≤ e Check:</span>
                      <strong style={{ color: numD <= numE ? 'var(--lime)' : '#f87171' }}>
                        {numD <= numE ? 'PASS (d ≤ e satisfied)' : 'FAIL (d > e violation)'}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Min ≤ Max Check:</span>
                      <strong style={{ color: numMin <= numMax ? 'var(--lime)' : '#f87171' }}>
                        {numMin <= numMax ? 'PASS (Min ≤ Max)' : 'FAIL (Min > Max)'}
                      </strong>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between' }}>
                  <button type="button" className="button button-outline" onClick={() => setCurrentStep(1)}>
                    <ArrowLeft style={{ width: '13px' }} /> Back
                  </button>
                  <button type="button" className="button" onClick={() => setCurrentStep(3)}>
                    Next: Capabilities <ArrowRight style={{ width: '13px' }} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: CAPABILITIES & RECEPTOR */}
            {currentStep === 3 && (
              <div>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Step 03 / Capabilities</span>
                    <h2>Receptor Geometry & Functional Facilities</h2>
                  </div>
                </div>

                <div className="choice-row">
                  <div>
                    <strong>Multiple Range Weighing Instrument</strong>
                    <span>Enables separate partial weighing ranges (Max₁, Max₂) under OIML R 76 Clause A.4.4.4.</span>
                  </div>
                  <div className="segmented">
                    <button
                      type="button"
                      className={!isMultipleRange ? 'selected' : ''}
                      onClick={() => setIsMultipleRange(false)}
                    >
                      Single Range
                    </button>
                    <button
                      type="button"
                      className={isMultipleRange ? 'selected' : ''}
                      onClick={() => setIsMultipleRange(true)}
                    >
                      Multiple Range
                    </button>
                  </div>
                </div>

                <div className="choice-row">
                  <div>
                    <strong>Load Receptor Support Points (N)</strong>
                    <span>Determines Clause A.4.7 eccentricity procedure (N ≤ 4 uses 4 quarter-segments; N &gt; 4 uses support points).</span>
                  </div>
                  <div className="segmented">
                    <button
                      type="button"
                      className={supportCount === 4 ? 'selected' : ''}
                      onClick={() => setSupportCount(4)}
                    >
                      N = 4 Points (A.4.7.1)
                    </button>
                    <button
                      type="button"
                      className={supportCount === 6 ? 'selected' : ''}
                      onClick={() => setSupportCount(6)}
                    >
                      N = 6 Points (A.4.7.2)
                    </button>
                  </div>
                </div>

                <div className="choice-row">
                  <div>
                    <strong>Tare Mechanism</strong>
                    <span>Subtractive tare device triggers Tare Balancing & Weighing evaluation (A.4.6).</span>
                  </div>
                  <select
                    value={tareType}
                    onChange={(e) => setTareType(e.target.value as TareType)}
                    style={{
                      background: '#0d110f',
                      border: '1px solid var(--line)',
                      borderRadius: '6px',
                      color: 'var(--ink)',
                      fontSize: '11px',
                      padding: '6px 12px',
                    }}
                  >
                    <option value="SUBTRACTIVE">Subtractive Tare</option>
                    <option value="ADDITIVE">Additive Tare</option>
                    <option value="NONE">No Tare Device</option>
                  </select>
                </div>

                <div className="choice-row">
                  <div>
                    <strong>Zero-Setting & Tracking Device</strong>
                    <span>Automatic/semi-automatic zero-setting triggers zero accuracy test under Clause A.4.2.</span>
                  </div>
                  <button
                    type="button"
                    className={`toggle ${hasZeroSetting ? 'on' : ''}`}
                    onClick={() => setHasZeroSetting(!hasZeroSetting)}
                    aria-label="Toggle zero setting"
                  >
                    <i aria-hidden="true" />
                  </button>
                </div>

                <div className="choice-row">
                  <div>
                    <strong>Electronic Instrument Construction</strong>
                    <span>Activates climatic influence tests (Temperature A.5.3.1, Voltage A.5.4, Warm-up A.5.2).</span>
                  </div>
                  <button
                    type="button"
                    className={`toggle ${isElectronic ? 'on' : ''}`}
                    onClick={() => setIsElectronic(!isElectronic)}
                    aria-label="Toggle electronic"
                  >
                    <i aria-hidden="true" />
                  </button>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between' }}>
                  <button type="button" className="button button-outline" onClick={() => setCurrentStep(2)}>
                    <ArrowLeft style={{ width: '13px' }} /> Back
                  </button>
                  <button
                    type="button"
                    className="button"
                    onClick={() => setCurrentStep(isMultipleRange ? 4 : 5)}
                  >
                    Next: {isMultipleRange ? 'Multi-Range Setup' : 'Review & Confirm'} <ArrowRight style={{ width: '13px' }} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 4: MULTIPLE RANGE SETUP (conditional) */}
            {currentStep === 4 && isMultipleRange && (
              <div>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Step 04 / Multiple Range</span>
                    <h2>Partial Weighing Ranges Specification (Clause A.4.4.4)</h2>
                  </div>
                  <Badge tone="lime">2 Partial Ranges</Badge>
                </div>

                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)', marginBottom: '20px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--warm)', fontWeight: 600, marginBottom: '12px' }}>
                    Partial Range 1 (Lower Range W₁)
                  </div>
                  <div className="field-grid">
                    <label>
                      Min₁
                      <input value={r1Min} onChange={(e) => setR1Min(e.target.value)} required />
                    </label>
                    <label>
                      Max₁
                      <input value={r1Max} onChange={(e) => setR1Max(e.target.value)} required />
                    </label>
                    <label>
                      Scale Interval e₁
                      <input value={r1E} onChange={(e) => setR1E(e.target.value)} required />
                    </label>
                    <label>
                      Resolution d₁
                      <input value={r1D} onChange={(e) => setR1D(e.target.value)} required />
                    </label>
                  </div>
                </div>

                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)', marginBottom: '20px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--warm)', fontWeight: 600, marginBottom: '12px' }}>
                    Partial Range 2 (Upper Range W₂)
                  </div>
                  <div className="field-grid">
                    <label>
                      Min₂
                      <input value={r2Min} onChange={(e) => setR2Min(e.target.value)} required />
                    </label>
                    <label>
                      Max₂
                      <input value={r2Max} onChange={(e) => setR2Max(e.target.value)} required />
                    </label>
                    <label>
                      Scale Interval e₂
                      <input value={r2E} onChange={(e) => setR2E(e.target.value)} required />
                    </label>
                    <label>
                      Resolution d₂
                      <input value={r2D} onChange={(e) => setR2D(e.target.value)} required />
                    </label>
                  </div>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between' }}>
                  <button type="button" className="button button-outline" onClick={() => setCurrentStep(3)}>
                    <ArrowLeft style={{ width: '13px' }} /> Back
                  </button>
                  <button type="button" className="button" onClick={() => setCurrentStep(5)}>
                    Next: Review & Confirm <ArrowRight style={{ width: '13px' }} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 5: REVIEW & METROLOGICAL VALIDATION */}
            {currentStep === 5 && (
              <div>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Step 05 / Review & Pre-Flight</span>
                    <h2>Metrological Validation & Pre-Registration Check</h2>
                  </div>
                  <Badge tone={validationErrors.length === 0 ? 'lime' : 'neutral'}>
                    {validationErrors.length === 0 ? 'Validation Passed' : `${validationErrors.length} Errors`}
                  </Badge>
                </div>

                {validationErrors.length > 0 ? (
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.08)',
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      borderRadius: '8px',
                      padding: '16px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 600, fontSize: '12px', marginBottom: '8px' }}>
                      <ShieldAlert style={{ width: '16px' }} />
                      Impossible configuration detected — cannot register:
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '20px', color: '#fca5a5', fontSize: '11px', lineHeight: 1.6 }}>
                      {validationErrors.map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div
                    style={{
                      background: 'rgba(182, 237, 78, 0.08)',
                      border: '1px solid rgba(182, 237, 78, 0.25)',
                      borderRadius: '8px',
                      padding: '16px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--lime)', fontWeight: 600, fontSize: '12px' }}>
                      <CheckCircle2 style={{ width: '16px' }} />
                      All OIML R 76-1:2006 physical & metrological constraints verified.
                    </div>
                  </div>
                )}

                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '16px', border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: '12px', color: 'var(--warm)', fontWeight: 600, marginBottom: '12px' }}>
                    Specification Summary
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '11px' }}>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Model & Manufacturer:</span>
                      <strong style={{ color: 'var(--ink)' }}>{modelName} ({manufacturer})</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Serial / Prototype:</span>
                      <strong style={{ color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>{serialNumber}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Accuracy Class:</span>
                      <strong style={{ color: 'var(--ink)' }}>{accuracyClass.replace('_', ' ')}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Capacity Limits:</span>
                      <strong style={{ color: 'var(--ink)' }}>Min: {minCapacity} {unit} · Max: {maxCapacity} {unit}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Scale Intervals:</span>
                      <strong style={{ color: 'var(--ink)' }}>e = {eInterval} {unit} · d = {dInterval} {unit}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Range Architecture:</span>
                      <strong style={{ color: isMultipleRange ? 'var(--lime)' : 'var(--ink)' }}>
                        {isMultipleRange ? 'Multiple Range (2 Partial Ranges)' : 'Single Range'}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Eccentricity Procedure:</span>
                      <strong style={{ color: 'var(--ink)' }}>
                        {supportCount <= 4 ? 'A.4.7.1 (4 Quarter-Segments)' : 'A.4.7.2 (N Support Points)'}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--dim)', display: 'block' }}>Tare & Zero Facilities:</span>
                      <strong style={{ color: 'var(--ink)' }}>
                        Tare: {tareType} · Zero Device: {hasZeroSetting ? 'Enabled' : 'Disabled'}
                      </strong>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between' }}>
                  <button
                    type="button"
                    className="button button-outline"
                    onClick={() => setCurrentStep(isMultipleRange ? 4 : 3)}
                  >
                    <ArrowLeft style={{ width: '13px' }} /> Back
                  </button>
                  <button
                    type="submit"
                    className="button"
                    disabled={validationErrors.length > 0 || submitting}
                    style={{
                      opacity: validationErrors.length > 0 || submitting ? 0.5 : 1,
                      cursor: validationErrors.length > 0 || submitting ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {submitting ? 'Registering...' : 'Register Instrument & Attach Configuration'} <Check style={{ width: '13px' }} />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Pre-Flight Applicability Impact */}
          <aside className="panel impact-panel" style={{ alignSelf: 'start' }}>
            <div className="impact-header">
              <div>
                <span className="eyebrow lime-text">Deterministic Applicability</span>
                <h2>Applicability Preview</h2>
              </div>
              <span className="engine-mark" aria-hidden="true">
                <ShieldCheck />
              </span>
            </div>

            <p style={{ color: 'var(--muted)', fontSize: '11px', lineHeight: 1.5, margin: '10px 0 20px' }}>
              The metrological parameters you specify directly drive test applicability under OIML R 76-1:2006.
            </p>

            <div className="ready-stat">
              <span>Standard</span>
              <strong>OIML R 76-1:2006 (E)</strong>
            </div>
            <div className="ready-stat">
              <span>Resolution (n)</span>
              <strong>{scaleIntervalsCount.toLocaleString()} intervals</strong>
            </div>
            <div className="ready-stat">
              <span>Primary Weighing</span>
              <strong>{isMultipleRange ? 'A.4.4.4 (Range 1 & Range 2)' : 'A.4.4 (Single Range)'}</strong>
            </div>
            <div className="ready-stat">
              <span>Eccentricity</span>
              <strong>{supportCount <= 4 ? 'A.4.7.1 (4 Quarters)' : 'A.4.7.2 (Support Points)'}</strong>
            </div>
            <div className="ready-stat">
              <span>Repeatability</span>
              <strong>A.4.10 (Series A & B)</strong>
            </div>
            <div className="ready-stat">
              <span>Tare Test</span>
              <strong>{tareType !== 'NONE' ? 'A.4.6 (Applicable)' : 'Not Applicable'}</strong>
            </div>
            <div className="ready-stat">
              <span>Zero-Setting Test</span>
              <strong>{hasZeroSetting ? 'A.4.2 (Applicable)' : 'Not Applicable'}</strong>
            </div>

            <div className="config-divider" />

            <div className="ready-stat">
              <span>Expected Procedures</span>
              <strong style={{ color: 'var(--lime)', fontSize: '14px' }}>
                {isMultipleRange ? '10 procedures (+2 partial)' : '09 procedures'}
              </strong>
            </div>
          </aside>
        </div>
      </form>
    </div>
  )
}
