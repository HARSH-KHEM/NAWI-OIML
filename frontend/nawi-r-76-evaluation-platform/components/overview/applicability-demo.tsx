'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  Check,
  CircleHelp,
  Gauge,
  Info,
  Sparkles,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { CANONICAL_PROCEDURES } from '@/lib/mock-data'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

type RangeMode = 'single' | 'multiple'

export function ApplicabilityDemo() {
  const containerRef = useRef<HTMLElement | null>(null)
  const impactCountRef = useRef<HTMLElement | null>(null)
  const [rangeMode, setRangeMode] = useState<RangeMode>('multiple')
  const [activeWhyId, setActiveWhyId] = useState<string | null>(null)

  // Filter canonical procedures dynamically based on single vs multiple range
  const applicableProcedures = useMemo(() => {
    return CANONICAL_PROCEDURES.filter((p) => {
      if (rangeMode === 'single') return p.applicableToSingleRange
      return p.applicableToMultipleRange
    })
  }, [rangeMode])

  const totalProcedures = CANONICAL_PROCEDURES.length

  // Initial scroll-triggered reveal
  useEffect(() => {
    if (!containerRef.current) return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 80%',
        },
        defaults: { ease: 'power3.out' },
      })

      tl.from('.instrument-strip', {
        opacity: 0,
        y: 20,
        duration: 0.6,
      })
        .from(
          '.config-form',
          {
            opacity: 0,
            x: -24,
            duration: 0.6,
          },
          '-=0.3'
        )
        .from(
          '.impact-panel',
          {
            opacity: 0,
            x: 24,
            duration: 0.6,
          },
          '-=0.4'
        )
        .from(
          '.procedure',
          {
            opacity: 0,
            y: 12,
            stagger: 0.05,
            duration: 0.4,
          },
          '-=0.2'
        )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  // Animate procedure list when mode toggles
  const handleRangeChange = (mode: RangeMode) => {
    if (mode === rangeMode) return
    setRangeMode(mode)

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    // Quick subtle pulse on impact count & new procedures
    if (impactCountRef.current) {
      gsap.fromTo(
        impactCountRef.current,
        { scale: 1.15, color: '#ffffff' },
        { scale: 1, color: 'var(--lime)', duration: 0.4, ease: 'power2.out' }
      )
    }

    gsap.fromTo(
      '.procedure',
      { opacity: 0.5, y: 4 },
      { opacity: 1, y: 0, stagger: 0.04, duration: 0.3, ease: 'power2.out' }
    )
  }

  return (
    <section className="overview-section" id="applicability-engine" ref={containerRef}>
      <div className="section-overline">
        02 · Deterministic Applicability Engine <span>USP INTERACTION</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>02</span>Instrument Configuration Drives The Workflow
          </div>
          <h2 style={{ margin: '8px 0', fontSize: 'clamp(28px, 4vw, 48px)', letterSpacing: '-0.05em' }}>
            The instrument configuration defines the test plan.
          </h2>
          <p>
            Toggle capabilities below. Watch the applicability engine deterministically recalculate
            applicable OIML R 76-1:2006 test procedures in real time.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/new" className="button">
            Configure new instrument <ArrowRight />
          </Link>
        </div>
      </div>

      {/* Active Instrument Strip */}
      <div className="instrument-strip">
        <div className="instrument-symbol" aria-hidden="true">
          <Gauge />
        </div>
        <div>
          <span className="eyebrow">Demo Configuration / SYNTH-DEMO-NAWI-001</span>
          <h2>
            ABC-300 Bench Scale <Badge tone="lime">Class III</Badge>
          </h2>
          <p>Non-automatic weighing instrument · OIML R 76-1:2006 (E)</p>
        </div>
        <div className="strip-spec">
          <span>Max Capacity</span>
          <strong>30.000 kg</strong>
        </div>
        <div className="strip-spec">
          <span>Min Capacity</span>
          <strong>0.200 kg</strong>
        </div>
        <div className="strip-spec">
          <span>Scale Interval (e)</span>
          <strong>0.010 kg (10 g)</strong>
        </div>
      </div>

      {/* Two-Column Configuration & Live Impact Layout */}
      <div className="config-layout">
        {/* Left Column: Capability Configuration Panel */}
        <div className="panel config-form">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Capability Settings</span>
              <h2>Instrument metrology parameters</h2>
            </div>
            <span className="autosave">
              <i aria-hidden="true" /> Real-time resolution
            </span>
          </div>

          <div className="field-grid">
            <label>
              Manufacturer
              <input value="Global Bench Metrology Systems" readOnly />
            </label>
            <label>
              Model Name
              <input value="ABC-300 Bench Scale" readOnly />
            </label>
            <label>
              Accuracy Class
              <select defaultValue="CLASS_III" disabled>
                <option value="CLASS_III">Class III (Medium Accuracy)</option>
              </select>
            </label>
            <label>
              Load Receptor Geometry
              <input value="4 Support Points (Quarter Segments)" readOnly />
            </label>
          </div>

          <div className="config-divider" />

          <div className="eyebrow" style={{ marginBottom: '12px' }}>
            Interactive Capability Triggers
          </div>

          {/* Multiple Range Toggle */}
          <div className="choice-row">
            <div>
              <strong>Multiple Range Capability</strong>
              <span>
                Enables separate partial weighing ranges (Max₁ = 15 kg, Max₂ = 30 kg) under A.4.4.4.
              </span>
            </div>
            <div className="segmented" role="radiogroup" aria-label="Multiple Range Selection">
              <button
                type="button"
                className={rangeMode === 'single' ? 'selected' : ''}
                onClick={() => handleRangeChange('single')}
                role="radio"
                aria-checked={rangeMode === 'single'}
              >
                Off (Single)
              </button>
              <button
                type="button"
                className={rangeMode === 'multiple' ? 'selected' : ''}
                onClick={() => handleRangeChange('multiple')}
                role="radio"
                aria-checked={rangeMode === 'multiple'}
              >
                On (Multi)
              </button>
            </div>
          </div>

          {/* Preset Tare Device */}
          <div className="choice-row">
            <div>
              <strong>Subtractive Tare Mechanism</strong>
              <span>Activates Tare Balancing and Weighing verification under clause A.4.6.</span>
            </div>
            <button className="toggle on" aria-label="Subtractive tare enabled" disabled>
              <i aria-hidden="true" />
            </button>
          </div>

          {/* Zero Setting */}
          <div className="choice-row">
            <div>
              <strong>Zero-Setting & Tracking Device</strong>
              <span>Activates Zero-Setting Range and Accuracy verification under clause A.4.2.</span>
            </div>
            <button className="toggle on" aria-label="Zero-setting enabled" disabled>
              <i aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Right Column: Live Applicability Engine Impact */}
        <div className="panel impact-panel">
          <div className="impact-header">
            <div>
              <span className="eyebrow lime-text">Live Applicability Engine</span>
              <h2>Executable plan consequences</h2>
            </div>
            <span className="engine-mark" aria-hidden="true">
              <Sparkles />
            </span>
          </div>

          <div className="impact-count">
            <strong ref={impactCountRef as any}>
              {String(applicableProcedures.length).padStart(2, '0')}
            </strong>
            <div>
              <span>applicable procedures</span>
              <small>
                {rangeMode === 'multiple'
                  ? '+2 partial range procedures activated (A.4.4.4)'
                  : 'single-range base procedure set only'}
              </small>
            </div>
          </div>

          <div className="impact-bar" aria-hidden="true">
            <i style={{ width: `${(applicableProcedures.length / totalProcedures) * 100}%` }} />
          </div>

          <div className="impact-labels">
            <span>INPUT: INSTRUMENT CONFIGURATION</span>
            <span>OUTPUT: {applicableProcedures.length} DETERMINISTIC PROCEDURES</span>
          </div>

          {/* Procedure List with Dynamic Added Badges */}
          <div className="procedure-list">
            {applicableProcedures.slice(0, 6).map((proc) => {
              const isMultiRangeSpecific = proc.scope === 'RANGE'
              const isWhyOpen = activeWhyId === proc.id

              return (
                <div className="procedure included" key={proc.id}>
                  <div className="proc-mark" aria-hidden="true">
                    <Check />
                  </div>
                  <div>
                    <strong>{proc.name}</strong>
                    <span>
                      {proc.r76Ref} · {proc.description}
                    </span>
                  </div>

                  {isMultiRangeSpecific && <Badge tone="lime">Multi-Range Added</Badge>}

                  <button
                    className="why"
                    onClick={() => setActiveWhyId(isWhyOpen ? null : proc.id)}
                    aria-label={`Why is ${proc.name} applicable?`}
                    title="Inspect R-76 applicability reasoning"
                  >
                    <CircleHelp />
                  </button>

                  {isWhyOpen && (
                    <div className="why-detail" role="tooltip">
                      <span>AUTHORITATIVE R-76 JUSTIFICATION</span>
                      <p>
                        <strong>Clause {proc.r76Ref}:</strong> {proc.whyApplicable}
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <div className="impact-footer">
            <Info aria-hidden="true" />
            <span>Plan derived deterministically via validated backend rules.</span>
            <Link href="/test-plans" className="impact-footer-link">
              View all {applicableProcedures.length} procedures <ArrowRight />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
