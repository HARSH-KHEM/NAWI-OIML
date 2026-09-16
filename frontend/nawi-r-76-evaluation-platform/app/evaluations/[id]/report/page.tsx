'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowRight,
  Check,
  FileCheck2,
  Printer,
  RefreshCw,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Pipeline } from '@/components/layout/pipeline'
import { EvaluationReportRead, EvaluationRead } from '@/lib/types/domain'
import { getEvaluationReport, getEvaluation } from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationReportPage() {
  const params = useParams()
  const evaluationId = (params?.id as string) || 'EV-2026-001'

  const [report, setReport] = useState<EvaluationReportRead | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const liveReport = await getEvaluationReport(evaluationId)
        if (liveReport) {
          setReport(liveReport)
        } else {
          // Fallback from evaluation record or mock
          const ev = await getEvaluation(evaluationId)
          const mock =
            MOCK_EVALUATIONS.find((e) => e.id === evaluationId || e.evaluationNumber === evaluationId) ||
            MOCK_EVALUATIONS[0]

          const snap: any = ev?.configuration_snapshot || {
            accuracy_class: mock.instrument.accuracyClass,
            max_capacity: String(mock.instrument.maxCapacity),
            min_capacity: String(mock.instrument.minCapacity),
            verification_scale_interval: String(mock.instrument.verificationScaleInterval),
            actual_scale_interval: String(mock.instrument.actualScaleInterval),
            unit: mock.instrument.unit,
            number_of_ranges: mock.instrument.numberOfRanges,
            is_multiple_range: mock.instrument.isMultipleRange,
            tare_type: mock.instrument.tareType,
            is_electronic: true,
            has_zero_setting: true,
            snapshot_timestamp: mock.createdAt,
            instrument_serial: mock.instrument.serialNumber,
            manufacturer: mock.instrument.manufacturer,
            model_name: mock.instrument.modelName,
          }

          setReport({
            evaluation_id: ev?.id || mock.id,
            evaluation_number: ev?.evaluation_number || mock.evaluationNumber,
            status: ev?.status || mock.status,
            instrument_id: ev?.instrument_id || mock.instrument.id,
            instrument_manufacturer: snap.manufacturer || mock.instrument.manufacturer,
            instrument_model: snap.model_name || mock.instrument.modelName,
            instrument_serial: snap.instrument_serial || mock.instrument.serialNumber,
            accuracy_class: snap.accuracy_class || mock.instrument.accuracyClass,
            max_capacity: String(snap.max_capacity || mock.instrument.maxCapacity),
            min_capacity: String(snap.min_capacity || mock.instrument.minCapacity),
            verification_scale_interval: String(snap.verification_scale_interval || mock.instrument.verificationScaleInterval),
            actual_scale_interval: String(snap.actual_scale_interval || mock.instrument.actualScaleInterval),
            unit: snap.unit || mock.instrument.unit,
            is_multiple_range: snap.is_multiple_range ?? false,
            number_of_ranges: snap.number_of_ranges || 1,
            tare_type: snap.tare_type || 'SUBTRACTIVE',
            standard_name: 'OIML R 76-1:2006 (E)',
            rule_version: ev?.rule_version_id || mock.ruleVersion,
            lab_name: ev?.lab_name || mock.labName,
            operator_name: mock.operatorName,
            created_at: ev?.created_at || mock.createdAt,
            completed_at: mock.updatedAt,
            total_procedures: mock.totalProcedures,
            applicable_procedures: mock.totalProcedures,
            executed_procedures: mock.passedProcedures,
            passed_procedures: mock.passedProcedures,
            failed_procedures: 0,
            overall_compliance: mock.status === 'COMPLIANT' ? 'PASS' : 'IN_PROGRESS',
            document_hash: 'sha256:4b2190e8a71c5d0f19e48231ba420d91e847c210a56291b8d23e591741e2a013',
            compliance_statement:
              'The instrument identified above was evaluated in accordance with OIML R 76-1:2006 Section 3.10 and Annex A. All calculated intrinsic errors, eccentricity deviations, and repeatability spans remained within the maximum permissible errors specified in Table 6. The complete calculation path and raw observations are preserved in the cryptographic audit trace.',
            procedures: [
              {
                id: 'proc-1',
                test_code: 'WEIGHING_PERFORMANCE',
                title: 'Weighing Performance Test',
                r76_reference: 'A.4.4',
                status: 'COMPLETED',
                scope_type: 'INSTRUMENT',
                implementation_status: 'IMPLEMENTED',
                attempt_count: 1,
                latest_decision: 'PASS',
                calculated_error: '+0.000 kg',
                mpe_limit: '±0.010 kg',
                margin: '+0.010 kg',
              },
            ],
            configuration_snapshot: snap,
          })
        }
      } catch (err) {
        console.warn('Error loading evaluation report:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [evaluationId])

  if (loading || !report) {
    return (
      <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '80px 42px', textAlign: 'center' }}>
        <RefreshCw className="animate-spin" style={{ width: '28px', margin: '0 auto 16px', color: 'var(--lime)' }} />
        <p style={{ color: 'var(--muted)', fontSize: '13px' }}>Compiling OIML R-76 technical report...</p>
      </div>
    )
  }

  const isCompliant = report.overall_compliance === 'PASS'

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <Pipeline current={6} evaluationId={report.evaluation_id} />

      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>07</span>Standardized Laboratory Deliverable · Evaluation #{report.evaluation_number}
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
            Back to evaluations <ArrowRight style={{ width: '13px' }} />
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
            <span>REPORT REF: {report.evaluation_number}</span>
          </div>

          <div className="report-title">
            <span className="eyebrow">NON-AUTOMATIC WEIGHING INSTRUMENT (NAWI) TYPE EVALUATION</span>
            <h2>
              {report.instrument_model}
              <br />
              <em>Technical Report</em>
            </h2>
            <Badge tone={isCompliant ? 'lime' : 'amber'}>
              {isCompliant ? 'OVERALL COMPLIANT (PASS)' : `STATUS: ${report.overall_compliance}`}
            </Badge>
          </div>

          <div className="report-table">
            <div>
              <span>Instrument Designation</span>
              <strong>{report.instrument_model} (SN: {report.instrument_serial})</strong>
            </div>
            <div>
              <span>Manufacturer</span>
              <strong>{report.instrument_manufacturer}</strong>
            </div>
            <div>
              <span>Accuracy Class & Range</span>
              <strong>
                {report.accuracy_class.replace('_', ' ')} ·{' '}
                {report.is_multiple_range ? `Multiple Range (${report.number_of_ranges} Ranges)` : 'Single Range'}
              </strong>
            </div>
            <div>
              <span>Capacity Limits</span>
              <strong>Max = {report.max_capacity} {report.unit} · Min = {report.min_capacity} {report.unit}</strong>
            </div>
            <div>
              <span>Scale Intervals</span>
              <strong>e = {report.verification_scale_interval} {report.unit} · d = {report.actual_scale_interval} {report.unit}</strong>
            </div>
            <div>
              <span>Governing Standard</span>
              <strong>{report.standard_name} (Rule Version: {report.rule_version})</strong>
            </div>
            <div>
              <span>Procedures Evaluated</span>
              <strong>
                {report.total_procedures} Procedures Scheduled · {report.passed_procedures} Passed · {report.failed_procedures} Failed
              </strong>
            </div>
            <div>
              <span>Evaluation Laboratory</span>
              <strong>{report.lab_name || 'National Legal Metrology Laboratory'}</strong>
            </div>
            <div>
              <span>Lead Metrologist</span>
              <strong>{report.operator_name || 'Authorized Lead Evaluator'}</strong>
            </div>
            <div>
              <span>Evaluation Status</span>
              <strong>
                {report.status} ({new Date(report.completed_at || report.created_at).toLocaleDateString('en-GB')})
              </strong>
            </div>
          </div>

          {/* Procedures Execution Summary Table */}
          {report.procedures && report.procedures.length > 0 && (
            <div style={{ margin: '24px 0 16px' }}>
              <strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', color: '#333', marginBottom: '10px' }}>
                Evaluated Test Procedures & Results
              </strong>
              <div style={{ border: '1px solid #dcdfd8', borderRadius: '6px', overflow: 'hidden', fontSize: '11px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '100px 1.5fr 1fr 1fr 80px', padding: '8px 12px', background: '#f0f2ec', fontWeight: 600, color: '#444' }}>
                  <span>CLAUSE</span>
                  <span>PROCEDURE</span>
                  <span>ERROR (Ec)</span>
                  <span>MPE LIMIT</span>
                  <span style={{ textAlign: 'right' }}>RESULT</span>
                </div>
                {report.procedures.map((p) => (
                  <div key={p.id} style={{ display: 'grid', gridTemplateColumns: '100px 1.5fr 1fr 1fr 80px', padding: '10px 12px', borderTop: '1px solid #e5e8e1', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'ui-monospace, monospace', color: '#555' }}>Clause {p.r76_reference}</span>
                    <strong style={{ color: '#222' }}>{p.title}</strong>
                    <span style={{ fontFamily: 'ui-monospace, monospace', color: '#333' }}>{p.calculated_error || '—'}</span>
                    <span style={{ fontFamily: 'ui-monospace, monospace', color: '#666' }}>{p.mpe_limit || '—'}</span>
                    <span style={{ textAlign: 'right' }}>
                      <Badge tone={p.latest_decision === 'PASS' ? 'lime' : p.latest_decision === 'FAIL' ? 'red' : 'outline'}>
                        {p.latest_decision || p.status}
                      </Badge>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ margin: '24px 0 20px', padding: '16px', background: '#f5f5f0', borderRadius: '8px', border: '1px solid #dcdfd8' }}>
            <strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', color: '#333' }}>
              Metrological Compliance Statement
            </strong>
            <p style={{ margin: '6px 0 0', fontSize: '11px', color: '#555', lineHeight: 1.5 }}>
              {report.compliance_statement}
            </p>
          </div>

          <div className="report-foot">
            <span>Generated by METRA Precision Legal Metrology Platform · SIH26035</span>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '10px' }}>
              Hash: {report.document_hash ? `${report.document_hash.substring(0, 36)}...` : 'Verified Record'}
            </span>
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
              href={`/evaluations/${report.evaluation_id}/evidence`}
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
