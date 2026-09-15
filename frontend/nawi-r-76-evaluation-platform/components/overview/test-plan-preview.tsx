'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowRight, Check, ChevronRight, Play, TestTube2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { CANONICAL_PROCEDURES } from '@/lib/mock-data'

export function TestPlanPreview() {
  const planItems = CANONICAL_PROCEDURES.filter((p) => p.status === 'IMPLEMENTED').slice(0, 4)

  return (
    <section className="overview-section" id="test-plan">
      <div className="section-overline">
        03 · Execution Plan <span>DERIVED DIRECTLY FROM THE SPECIFICATION</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>03</span>Authoritative Execution Schedule
          </div>
          <h2 style={{ margin: '8px 0', fontSize: 'clamp(28px, 4vw, 48px)', letterSpacing: '-0.05em' }}>
            A plan derived from the instrument.
          </h2>
          <p>
            No guesswork in the laboratory. Each test step is generated with exact test loads,
            required loading positions, and Table 6 permissible error thresholds.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/test-plans" className="button button-secondary">
            Master test catalog <ArrowRight />
          </Link>
          <Link href="/evaluations/EV-2026-001/plan" className="button">
            Open active plan <Play />
          </Link>
        </div>
      </div>

      <div className="plan-layout">
        {/* Main Plan Panel */}
        <div className="panel plan-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow lime-text">Execution Sequence</span>
              <h2>Primary Performance Tests · Single Range (Class III)</h2>
            </div>
            <Badge tone="lime">Validated Phase 2 Scope</Badge>
          </div>

          <div className="plan-items-container">
            {planItems.map((proc, index) => (
              <div className="plan-item" key={proc.id}>
                <span className="plan-num">{String(index + 1).padStart(2, '0')}</span>
                <div className="plan-icon" aria-hidden="true">
                  <TestTube2 />
                </div>
                <div className="plan-copy">
                  <strong>{proc.name}</strong>
                  <span>OIML R 76-1:2006 · Clause {proc.r76Ref}</span>
                  <p>{proc.description}</p>
                </div>
                <div className="plan-state">
                  <Badge tone={index === 0 ? 'lime' : 'outline'}>
                    {index === 0 ? 'Ready to run' : 'Queued'}
                  </Badge>
                  <span>{index === 0 ? '12 min' : '08 min'}</span>
                </div>
                <ChevronRight className="plan-chevron" aria-hidden="true" />
              </div>
            ))}
          </div>
        </div>

        {/* Readiness Aside */}
        <aside className="panel readiness-panel">
          <span className="eyebrow">Evaluation Readiness</span>
          <h2>Execution inputs verified</h2>

          <div className="ready-row">
            <Check aria-hidden="true" />
            <span>Instrument configuration frozen</span>
          </div>
          <div className="ready-row">
            <Check aria-hidden="true" />
            <span>Rule version locked: R-76-1:2006</span>
          </div>
          <div className="ready-row">
            <Check aria-hidden="true" />
            <span>Support points: 4 quarters resolved</span>
          </div>
          <div className="ready-row">
            <Check aria-hidden="true" />
            <span>Table 6 MPE tiers precomputed</span>
          </div>

          <div className="config-divider" />

          <div className="ready-stat">
            <span>Estimated execution</span>
            <strong>~48 min total</strong>
          </div>
          <div className="ready-stat">
            <span>Target compliance</span>
            <strong>OIML R 76 Class III</strong>
          </div>

          <Link href="/evaluations/EV-2026-001/tests/test-wp-01" className="button" style={{ width: '100%', justifyContent: 'center', marginTop: '16px' }}>
            Start guided test <Play />
          </Link>
        </aside>
      </div>
    </section>
  )
}
