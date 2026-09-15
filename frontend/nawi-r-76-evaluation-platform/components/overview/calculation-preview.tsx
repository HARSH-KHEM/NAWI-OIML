'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Check, ChevronDown, ShieldCheck, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export function CalculationPreview() {
  const [revealPath, setRevealPath] = useState(true)

  return (
    <section className="overview-section" id="deterministic-compliance">
      <div className="section-overline">
        04 · Deterministic Compliance <span>VERIFIED ARITHMETIC</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>04</span>Defensible, Explainable Legal Metrology
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
            <div>
              <span>CORRECTED ERROR (Ec)</span>
              <strong>+0.002 kg</strong>
            </div>
            <b>≤</b>
            <div>
              <span>MAX PERMISSIBLE ERROR (MPE)</span>
              <strong>±0.010 kg</strong>
            </div>
            <div className="equation-pass">
              <Check aria-hidden="true" />
              <span>PASS</span>
            </div>
          </div>

          <button
            className="reveal-button"
            onClick={() => setRevealPath(!revealPath)}
            aria-expanded={revealPath}
          >
            {revealPath ? 'Hide calculation breakdown' : 'Reveal calculation breakdown'}
            <ChevronDown style={{ transform: revealPath ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>

          {revealPath && (
            <div className="calc-path">
              <div>
                <span>Observed Indication (I)</span>
                <strong>10.000 kg</strong>
              </div>
              <div>
                <span>Half Scale Interval (+ ½ e)</span>
                <strong>+0.005 kg (e = 0.010 kg)</strong>
              </div>
              <div>
                <span>Turning Point Weights (- ΔL)</span>
                <strong>-0.003 kg</strong>
              </div>
              <div>
                <span>Calculated Indication Prior to Rounding (P = I + ½e - ΔL)</span>
                <strong>10.002 kg</strong>
              </div>
              <div>
                <span>Test Load (L)</span>
                <strong>10.000 kg</strong>
              </div>
              <div>
                <span>Gross Error (E = P - L)</span>
                <strong>+0.002 kg</strong>
              </div>
              <div>
                <span>Zero Error (E0)</span>
                <strong>+0.000 kg</strong>
              </div>
              <div className="path-result">
                <span>Corrected Error (Ec = E - E0)</span>
                <strong>+0.002 kg</strong>
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
