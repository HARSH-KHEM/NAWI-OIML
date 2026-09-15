'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowRight, FileCheck2, ShieldCheck, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export function CtaSection() {
  return (
    <section className="overview-section" id="report-cta">
      <div className="section-overline">
        06 · Complete Report Package <span>STANDARDIZED OIML R-76 REPORT</span>
      </div>

      <div className="report-layout">
        {/* Printable Report Sheet Mockup */}
        <div className="report-sheet">
          <div className="report-mast">
            <div className="wordmark">
              <span className="wordmark-mark" aria-hidden="true">
                <Zap />
              </span>
              <span>
                METRA
                <small>R-76 / EVALUATION ENGINE</small>
              </span>
            </div>
            <span>OFFICIAL CERTIFICATE FORMAT · EV-2026-001</span>
          </div>

          <div className="report-title">
            <span className="eyebrow">TYPE EVALUATION CERTIFICATE / 14 SEPTEMBER 2026</span>
            <h2>
              ABC-300 Bench Scale
              <br />
              <em>Compliance Record</em>
            </h2>
            <Badge tone="lime">COMPLIANT UNDER OIML R 76-1:2006</Badge>
          </div>

          <div className="report-table">
            <div>
              <span>Instrument Specification</span>
              <strong>Class III · Max 30.000 kg · Min 0.200 kg · e 0.010 kg</strong>
            </div>
            <div>
              <span>Configuration Profile</span>
              <strong>Single-Range Subtractive Tare · Electronic Indicator</strong>
            </div>
            <div>
              <span>Applicable Procedures</span>
              <strong>09 Procedures Evaluated · 09 Passed (0 Violations)</strong>
            </div>
            <div>
              <span>Authoritative Standard</span>
              <strong>OIML R 76-1: 2006 (E) · Section 3.10 & Annex A</strong>
            </div>
          </div>

          <div className="report-foot">
            <span>Deterministic Legal Metrology Engine · SIH26035</span>
            <span>Digital Certificate Hash: sha256:4b2190...</span>
          </div>
        </div>

        {/* Action Panel on Right */}
        <aside className="panel report-side">
          <span className="eyebrow">Export Package</span>
          <h2>Certified Evaluation Deliverables</h2>

          <div className="report-item">
            <span>01</span>
            <span>Instrument Identity & Verification Plate</span>
            <ShieldCheck aria-hidden="true" />
          </div>
          <div className="report-item">
            <span>02</span>
            <span>Frozen Metrological Configuration Snapshot</span>
            <ShieldCheck aria-hidden="true" />
          </div>
          <div className="report-item">
            <span>03</span>
            <span>Applicable Test Plan & Rule References</span>
            <ShieldCheck aria-hidden="true" />
          </div>
          <div className="report-item">
            <span>04</span>
            <span>Raw Observations & Calculated Turning Points</span>
            <ShieldCheck aria-hidden="true" />
          </div>
          <div className="report-item">
            <span>05</span>
            <span>Table 6 Compliance Verification Results</span>
            <ShieldCheck aria-hidden="true" />
          </div>
          <div className="report-item">
            <span>06</span>
            <span>End-to-End Cryptographic Evidence Trace</span>
            <ShieldCheck aria-hidden="true" />
          </div>

          <div style={{ marginTop: '28px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <Link href="/evaluations/EV-2026-001/report" className="button" style={{ justifyContent: 'center' }}>
              View full report preview <FileCheck2 />
            </Link>
            <Link href="/evaluations/new" className="button button-secondary" style={{ justifyContent: 'center' }}>
              Start new evaluation <ArrowRight />
            </Link>
          </div>
        </aside>
      </div>
    </section>
  )
}
