'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Check, ChevronDown, ShieldCheck, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export function CalculationPreview() {
  const containerRef = useRef<HTMLElement | null>(null)
  const [revealPath, setRevealPath] = useState(true)

  useEffect(() => {
    if (!containerRef.current) return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 75%',
        },
        defaults: { ease: 'power3.out' },
      })

      // 1. Decision banner & panels enter
      tl.from('.decision-banner', {
        opacity: 0,
        y: 20,
        duration: 0.6,
      })
        .from(
          '.calculation-panel',
          {
            opacity: 0,
            x: -20,
            duration: 0.5,
          },
          '-=0.3'
        )
        .from(
          '.decision-detail',
          {
            opacity: 0,
            x: 20,
            duration: 0.5,
          },
          '-=0.4'
        )

      // 2. Sequential arithmetic path animation: I -> P -> E -> Ec -> MPE -> PASS
      tl.from(
        '.calc-step',
        {
          opacity: 0,
          x: -12,
          stagger: 0.08,
          duration: 0.35,
        },
        '-=0.1'
      )

      // 3. Equation terms reveal
      tl.from(
        '.equation-term',
        {
          opacity: 0,
          scale: 0.9,
          stagger: 0.1,
          duration: 0.4,
        },
        '-=0.1'
      )

      // 4. Final PASS badge pops in AFTER calculation elements are revealed
      tl.from(
        '.equation-pass',
        {
          opacity: 0,
          scale: 1.3,
          duration: 0.4,
          ease: 'back.out(2)',
        },
        '+=0.1'
      )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section className="overview-section" id="deterministic-compliance" ref={containerRef}>
      <div className="section-overline">
        05 · Deterministic Compliance <span>VERIFIED ARITHMETIC</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>05</span>Defensible, Explainable Legal Metrology
          </div>
          <h2 style={{ margin: '8px 0', fontSize: 'clamp(28px, 4vw, 48px)', letterSpacing: '-0.05em' }}>
            The instrument passes by deterministic calculation.
          </h2>
          <p>
            No AI guesswork or black-box predictions. Compliance is computed using verified decimal
            arithmetic against OIML R 76-1:2006 Table 6 maximum permissible errors.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/EV-2026-001/compliance" className="button">
            View compliance engine <ArrowRight />
          </Link>
        </div>
      </div>

      {/* Decision Banner */}
      <div className="decision-banner">
        <div className="decision-icon" aria-hidden="true">
          <ShieldCheck />
        </div>
        <div>
          <Badge tone="lime">PASS / COMPLIANT</Badge>
          <h2>All intrinsic error requirements satisfied.</h2>
          <p>
            ABC-300 Bench Scale meets Table 6 MPE limits at all test loads up to Max capacity (30 kg).
          </p>
        </div>
        <strong>
          09 / 09
          <span>procedures passed</span>
        </strong>
      </div>

      <div className="result-layout">
        {/* Calculation Details Panel */}
        <div className="panel calculation-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">A.4.4.3 Calculation Formula</span>
              <h2>Weighing Performance Intrinsic Error</h2>
            </div>
            <Badge tone="lime">Within Table 6 Tolerance</Badge>
          </div>

          <div className="equation">
            <div className="equation-term">
              <span>CORRECTED ERROR (Ec)</span>
              <strong>+0.002 kg</strong>
            </div>
            <b className="equation-term">≤</b>
            <div className="equation-term">
              <span>MAX PERMISSIBLE ERROR (MPE)</span>
              <strong>±0.010 kg</strong>
            </div>
            <div className="equation-pass">
              <Check aria-hidden="true" />
              <span>PASS</span>
            </div>
          </div>

          <button
            type="button"
            className="reveal-button"
            onClick={() => setRevealPath(!revealPath)}
            aria-expanded={revealPath}
          >
            {revealPath ? 'Hide calculation breakdown' : 'Reveal calculation breakdown'}
            <ChevronDown style={{ transform: revealPath ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>

          {revealPath && (
            <div className="calc-path">
              <div className="calc-step">
                <span>1. Observed Indication (I)</span>
                <strong>10.000 kg</strong>
              </div>
              <div className="calc-step">
                <span>2. Half Scale Interval (+ ½ e)</span>
                <strong>+0.005 kg (e = 0.010 kg)</strong>
              </div>
              <div className="calc-step">
                <span>3. Turning Point Weights (- ΔL)</span>
                <strong>-0.003 kg</strong>
              </div>
              <div className="calc-step" style={{ background: '#182017', padding: '8px 10px' }}>
                <span>4. Indication Prior to Rounding (P = I + ½e - ΔL)</span>
                <strong style={{ color: 'var(--lime)' }}>10.002 kg</strong>
              </div>
              <div className="calc-step">
                <span>5. Test Load (L)</span>
                <strong>10.000 kg</strong>
              </div>
              <div className="calc-step">
                <span>6. Gross Error (E = P - L)</span>
                <strong>+0.002 kg</strong>
              </div>
              <div className="calc-step">
                <span>7. Zero-Load Error (E0)</span>
                <strong>+0.000 kg</strong>
              </div>
              <div className="calc-step path-result" style={{ background: '#1c261a', padding: '10px' }}>
                <span>8. Final Corrected Error (Ec = E - E0)</span>
                <strong style={{ color: 'var(--lime)' }}>+0.002 kg</strong>
              </div>
              <p style={{ marginTop: '12px' }}>
                Criterion: Under OIML R 76-1:2006 Table 6 for Class III with test load L = 10 kg
                (m = 1,000 e), MPE = ±1.0 e = ±0.010 kg. Since |+0.002 kg| ≤ 0.010 kg, result is PASS.
              </p>
            </div>
          )}
        </div>

        {/* Decision Detail Aside */}
        <aside className="panel decision-detail">
          <span className="eyebrow">Decision Verification</span>
          <h2>Rule & Audit Record</h2>

          <div className="detail-row">
            <span>Governing Standard</span>
            <strong>OIML R 76-1:2006 (E)</strong>
          </div>
          <div className="detail-row">
            <span>Accuracy Class</span>
            <strong>Class III (Medium)</strong>
          </div>
          <div className="detail-row">
            <span>Calculated Test Load</span>
            <strong>10.000 kg (1,000 e)</strong>
          </div>
          <div className="detail-row">
            <span>Applied Tolerance</span>
            <strong>±0.010 kg (±1.0 e)</strong>
          </div>
          <div className="detail-row">
            <span>Evaluation Engine</span>
            <strong>Python Decimal Pure AST</strong>
          </div>

          <div className="deterministic">
            <Zap aria-hidden="true" /> No AI inference. Zero hallucinations.
          </div>
        </aside>
      </div>
    </section>
  )
}
