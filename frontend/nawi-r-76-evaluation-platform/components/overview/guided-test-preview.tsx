'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Check, Play, TestTube2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export function GuidedTestPreview() {
  const containerRef = useRef<HTMLElement | null>(null)
  const [observedIndication, setObservedIndication] = useState('100.021')

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

      tl.from('.test-rail', {
        opacity: 0,
        x: -24,
        duration: 0.6,
      })
        .from(
          '.test-panel',
          {
            opacity: 0,
            x: 24,
            duration: 0.6,
          },
          '-=0.4'
        )
        .from(
          '.observation-field',
          {
            opacity: 0,
            y: 16,
            stagger: 0.1,
            duration: 0.4,
          },
          '-=0.2'
        )
        .from(
          '.validation-note',
          {
            opacity: 0,
            y: 10,
            duration: 0.4,
          },
          '-=0.1'
        )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section className="overview-section" id="guided-testing" ref={containerRef}>
      <div className="section-overline">
        04 · Guided Laboratory Execution <span>OPERATOR WORKSPACE</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>04</span>Standardized Guided Observation Capture
          </div>
          <h2 style={{ margin: '8px 0', fontSize: 'clamp(28px, 4vw, 48px)', letterSpacing: '-0.05em' }}>
            Structured laboratory test execution.
          </h2>
          <p>
            Operators follow step-by-step procedural guidelines with automatic range checks,
            unit normalization, and immutable audit timestamps.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/EV-2026-001/tests/test-wp-01" className="button">
            Enter test workspace <Play />
          </Link>
        </div>
      </div>

      <div className="test-layout">
        {/* Left Progress Rail */}
        <aside className="panel test-rail">
          <span className="eyebrow">Procedure Progress</span>
          <div className="rail-progress" aria-hidden="true">
            <i style={{ width: '20%' }} />
          </div>
          <strong>
            02 <span>/ 09 procedures</span>
          </strong>

          <div className="rail-procedure">
            <span>
              <Check style={{ width: '11px' }} />
            </span>
            <span>Weighing Performance (A.4.4)</span>
          </div>
          <div className="rail-procedure current">
            <span>
              <Play style={{ width: '10px' }} />
            </span>
            <span>Eccentric Loading (A.4.7)</span>
          </div>
          <div className="rail-procedure">
            <span>03</span>
            <span>Repeatability (A.4.10)</span>
          </div>
          <div className="rail-procedure">
            <span>04</span>
            <span>Tare Mechanism (A.4.6)</span>
          </div>
        </aside>

        {/* Main Test Workstation Panel */}
        <div className="panel test-panel">
          <div className="test-meta">
            <Badge tone="outline">P-02</Badge>
            <span>OIML R 76-1:2006 · Clause A.4.7</span>
            <span className="test-meta-right">HUMAN OBSERVATION · IMMUTABLE CAPTURE</span>
          </div>

          <div className="test-title" style={{ margin: '30px 0 25px' }}>
            <span className="eyebrow lime-text">Execution Step 01 / 04</span>
            <h3 style={{ margin: '8px 0', fontSize: '26px', color: 'var(--warm)' }}>
              Apply test load at Quarter-Segment 1
            </h3>
            <p>
              Apply test load L = 1/3 Max (10.000 kg) centrally on quarter-segment 1 of the load receptor.
              Wait for stability indication, then capture the displayed reading.
            </p>
          </div>

          {/* Observation Fields Grid */}
          <div className="observation-grid">
            <div className="observation-field">
              <label>
                Applied Load <span>kg</span>
              </label>
              <strong>10.000</strong>
              <small>Calculated procedure load (1/3 Max)</small>
            </div>

            <div className="observation-field active-field">
              <label>
                Observed Indication (I) <span>kg</span>
              </label>
              <input
                type="text"
                value={observedIndication}
                onChange={(e) => setObservedIndication(e.target.value)}
                aria-label="Observed indication in kilograms"
              />
              <small>Interactive test entry</small>
            </div>

            <div className="observation-field">
              <label>
                Zero-Load Error (E0) <span>kg</span>
              </label>
              <strong>+0.000</strong>
              <small>From pre-test zero verification</small>
            </div>
          </div>

          {/* Real-Time Input Validation Note */}
          <div className="validation-note">
            <Check aria-hidden="true" />
            <div>
              <strong>Observation verified within permissible physical bounds.</strong>
              <span>
                Value will be normalized and evaluated deterministically against Table 6 MPE limits.
              </span>
            </div>
          </div>

          <div className="test-bottom">
            <Link href="/evaluations/EV-2026-001/compliance" className="button">
              Evaluate calculation path <ArrowRight />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
