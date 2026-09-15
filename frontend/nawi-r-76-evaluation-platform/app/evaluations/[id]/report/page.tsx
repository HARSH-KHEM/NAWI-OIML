'use client'

import React from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  FileCheck2,
  Printer,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationReportPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'
  const evaluation =
    MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
    MOCK_EVALUATIONS[0]
  const inst = evaluation.instrument

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={6} evaluationId={evaluation.id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>07</span>Standardized Laboratory Deliverable
          </div>
          <h1>OIML R-76 Technical Evaluation Report</h1>
          <p>
            Standardized technical evaluation report generated from frozen configuration, verified observations,
            and deterministic compliance calculations.
          </p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="button button-secondary"
            onClick={() => window.print()}
          >
            <Printer style={{ width: '14px' }} /> Print / Export PDF
          </button>
          <Link href="/evaluations" className="button">
            Back to evaluations <ArrowRight />
          </Link>
        </div>
      </div>

      <div className="report-layout">
        {/* Main Printable Sheet */}
        <section className="report-sheet">
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
            <span>REPORT REF: {evaluation.evaluationNumber}</span>
          </div>

          <div className="report-title">
            <span className="eyebrow">NON-AUTOMATIC WEIGHING INSTRUMENT (NAWI) TYPE EVALUATION</span>
            <h2>
              {inst.modelName}
              <br />
              <em>Technical Report</em>
            </h2>
            <Badge tone="lime">OVERALL COMPLIANT (PASS)</Badge>
          </div>

          <div className="report-table">
            <div>
              <span>Instrument Designation</span>
              <strong>{inst.modelName} (SN: {inst.serialNumber})</strong>
            </div>
            <div>
              <span>Manufacturer</span>
              <strong>{inst.manufacturer}</strong>
            </div>
            <div>
              <span>Accuracy Class & Range</span>
              <strong>{inst.accuracyClass.replace('_', ' ')} · Single Range</strong>
            </div>
            <div>
              <span>Capacity Limits</span>
              <strong>Max = {inst.maxCapacity} {inst.unit} · Min = {inst.minCapacity} {inst.unit}</strong>
            </div>
            <div>
              <span>Scale Intervals</span>
              <strong>e = {inst.verificationScaleInterval} {inst.unit} · d = {inst.actualScaleInterval} {inst.unit}</strong>
            </div>
            <div>
              <span>Governing Standard</span>
              <strong>{evaluation.ruleVersion} (Standard Reference: OIML R 76-1:2006 (E))</strong>
            </div>
            <div>
              <span>Procedures Evaluated</span>
              <strong>{evaluation.totalProcedures} Procedures Tested · {evaluation.passedProcedures} Compliant · 0 Violations</strong>
            </div>
            <div>
              <span>Evaluation Laboratory</span>
              <strong>{evaluation.labName}</strong>
            </div>
            <div>
              <span>Lead Metrologist</span>
              <strong>{evaluation.operatorName}</strong>
            </div>
            <div>
              <span>Evaluation Status</span>
              <strong>COMPLETED & SEALED (14 September 2026)</strong>
            </div>
          </div>

          <div style={{ margin: '32px 0 20px', padding: '16px', background: '#f5f5f0', borderRadius: '8px', border: '1px solid #dcdfd8' }}>
            <strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', color: '#333' }}>
              Metrological Compliance Statement
            </strong>
            <p style={{ margin: '6px 0 0', fontSize: '11px', color: '#555', lineHeight: 1.5 }}>
              The instrument identified above was evaluated in accordance with OIML R 76-1:2006 Section 3.10 and Annex A.
              All calculated intrinsic errors, eccentricity deviations, and repeatability spans remained within the maximum
              permissible errors specified in Table 6. The complete calculation path and raw observations are preserved in the cryptographic audit trace.
            </p>
          </div>

          <div className="report-foot">
            <span>Generated by METRA Precision Legal Metrology Platform · SIH26035</span>
            <span>Document Hash: sha256:4b2190... · Verified Record</span>
          </div>
        </section>

        {/* Right Aside Package Breakdown */}
        <aside className="panel report-side">
          <span className="eyebrow">Report Structure</span>
          <h2>Certified Contents</h2>

          <div className="report-item">
            <span>01</span>
            <span>Instrument Identity & Verification Plate</span>
            <Check />
          </div>
          <div className="report-item">
            <span>02</span>
            <span>Frozen Configuration Snapshot</span>
            <Check />
          </div>
          <div className="report-item">
            <span>03</span>
            <span>Applicable Test Plan & Rule References</span>
            <Check />
          </div>
          <div className="report-item">
            <span>04</span>
            <span>Raw Observations & Corrected Errors</span>
            <Check />
          </div>
          <div className="report-item">
            <span>05</span>
            <span>Table 6 Compliance Decisions</span>
            <Check />
          </div>
          <div className="report-item">
            <span>06</span>
            <span>Cryptographic Traceability Hash</span>
            <Check />
          </div>

          <div style={{ marginTop: '32px' }}>
            <Link
              href={`/evaluations/${evaluation.id}/evidence`}
              className="button button-secondary"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              Back to evidence trace
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
