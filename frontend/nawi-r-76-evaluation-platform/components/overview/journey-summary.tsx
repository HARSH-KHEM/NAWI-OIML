'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowRight, GitBranch, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export function JourneySummary() {
  const steps = [
    { num: '01', title: 'Configure', desc: 'Define metrological capacity' },
    { num: '02', title: 'Applicability', desc: 'Resolve active R-76 rules' },
    { num: '03', title: 'Test Plan', desc: 'Generate execution schedule' },
    { num: '04', title: 'Execute', desc: 'Capture raw observations' },
    { num: '05', title: 'Calculate', desc: 'Compute error & MPE' },
    { num: '06', title: 'Evidence', desc: 'Link immutable audit trail' },
    { num: '07', title: 'Report', desc: 'Publish certified report' },
  ]

  return (
    <section className="overview-flow">
      <div className="section-overline">
        The Evaluation Pipeline <span>01—07 SEQUENTIAL WORKFLOW</span>
      </div>

      <div className="flow-line" role="list">
        {steps.map((step, i) => (
          <div className="flow-item" key={step.num} role="listitem">
            <span>{step.num}</span>
            <strong>{step.title}</strong>
            {i < steps.length - 1 && <ArrowRight aria-hidden="true" />}
          </div>
        ))}
      </div>

      <div className="editorial-grid">
        {/* Active Evaluation Card (Large Lime) */}
        <div className="evaluation-card large">
          <div>
            <Badge tone="neutral">Active Evaluation</Badge>
            <span className="card-index">EV-2026-001</span>
          </div>
          <h2>ABC-300</h2>
          <p>
            Non-automatic weighing instrument
            <br />
            Class III · 30.000 kg capacity · e = 10 g
          </p>
          <Link href="/evaluations/EV-2026-001" className="button" style={{ color: 'var(--black)', background: '#0b0d0c15', border: '1px solid #0b0d0c30' }}>
            Resume evaluation workspace <ArrowRight />
          </Link>
          <div className="card-foot">
            <span>Single-Range Configuration Frozen</span>
            <strong>STAGE 04 / 07</strong>
          </div>
        </div>

        {/* Latest Decision Card (Dark Panel) */}
        <div className="evaluation-card dark">
          <div className="card-topline">
            <span>Deterministic Result</span>
            <ShieldCheck style={{ color: 'var(--lime)' }} aria-hidden="true" />
          </div>
          <strong className="decision">COMPLIANT</strong>
          <p>All Table 6 permissible error limits satisfied under OIML R 76-1:2006.</p>
          <div className="decision-rule">
            EV-2026-001 <span>·</span> 14 SEP 2026
          </div>
        </div>

        {/* Evidence Chain Card (Outlined) */}
        <div className="evaluation-card outlined">
          <div className="card-topline">
            <span>Evidence Graph</span>
            <GitBranch style={{ color: 'var(--lime)' }} aria-hidden="true" />
          </div>
          <strong className="big-number">07</strong>
          <p>
            Cryptographically linked records
            <br />
            ready for auditor inspection.
          </p>
          <Link href="/evaluations/EV-2026-001/evidence" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--lime)', marginTop: 'auto', fontSize: '11px', fontWeight: 700 }}>
            Inspect trace chain <ArrowRight style={{ width: '13px' }} />
          </Link>
        </div>
      </div>
    </section>
  )
}
