'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  ArrowRight,
  Check,
  Gauge,
  Info,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'

export default function NewEvaluationPage() {
  const router = useRouter()

  // Form states matching backend InstrumentConfiguration model
  const [modelName, setModelName] = useState('ABC-300 Bench Scale')
  const [serialNumber, setSerialNumber] = useState('SYNTH-DEMO-NAWI-001-SN')
  const [accuracyClass, setAccuracyClass] = useState<'CLASS_I' | 'CLASS_II' | 'CLASS_III' | 'CLASS_IIII'>('CLASS_III')
  const [maxCapacity, setMaxCapacity] = useState('30.000')
  const [minCapacity, setMinCapacity] = useState('0.200')
  const [eInterval, setEInterval] = useState('0.010')
  const [dInterval, setDInterval] = useState('0.010')
  const [unit, setUnit] = useState('kg')
  const [isMultipleRange, setIsMultipleRange] = useState(false)
  const [hasTare, setHasTare] = useState(true)
  const [hasZero, setHasZero] = useState(true)
  const [supportCount, setSupportCount] = useState(4)
  const [ruleVersion, setRuleVersion] = useState('2006-01')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Redirect to the evaluation overview hub with the simulated/live record
    router.push('/evaluations/EV-2026-001')
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
          <h1>Configure Instrument</h1>
          <p>
            The metrological specification entered here determines test applicability under OIML R 76.
            Upon initialization, this configuration is captured as an immutable snapshot for audit integrity.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="config-layout">
          {/* Main Form Fields */}
          <div className="panel config-form">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Instrument Identity</span>
                <h2>Identification & Verification Plate</h2>
              </div>
              <Badge tone="lime">Synthetic Demonstration</Badge>
            </div>

            <div className="field-grid">
              <label>
                Manufacturer
                <input defaultValue="[SYNTHETIC] Global Bench Metrology Systems" readOnly />
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
                Governing Rule Version
                <select value={ruleVersion} onChange={(e) => setRuleVersion(e.target.value)}>
                  <option value="2006-01">OIML R 76-1: 2006 (E) · Active Standard</option>
                </select>
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
              <strong>OIML R 76-1:2006</strong>
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
              style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '12px' }}
            >
              Initialize evaluation & freeze snapshot <ArrowRight />
            </button>
          </aside>
        </div>
      </form>
    </div>
  )
}
