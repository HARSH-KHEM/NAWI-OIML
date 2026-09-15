'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  Check,
  FileCheck2,
  Printer,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function ReportsArchivePage() {
  const [searchQuery, setSearchQuery] = useState('')

  const reports = MOCK_EVALUATIONS.filter((e) => e.status === 'COMPLIANT')

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>04</span>Evaluation Certificates & Technical Records
          </div>
          <h1>Technical Evaluation Reports</h1>
          <p>
            Standardized technical reports generated under OIML R 76-1:2006.
            Each report compiles frozen instrument specifications, raw observations, and deterministic calculation results.
          </p>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="editorial-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {reports.map((ev) => (
          <div key={ev.id} className="panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
              <div>
                <span className="eyebrow lime-text">REPORT REF: {ev.evaluationNumber}</span>
                <h2 style={{ fontSize: '20px', margin: '6px 0 4px', color: 'var(--warm)' }}>
                  {ev.instrument.modelName}
                </h2>
                <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                  Standard: {ev.ruleVersion}
                </span>
              </div>
              <Badge tone="lime">COMPLIANT</Badge>
            </div>

            <p style={{ color: 'var(--muted)', fontSize: '12px', margin: '16px 0 20px', lineHeight: 1.5 }}>
              {ev.summary}
            </p>

            <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '14px', border: '1px solid var(--line)', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '8px' }}>
                <span style={{ color: 'var(--dim)' }}>Instrument Serial:</span>
                <strong style={{ color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>{ev.instrument.serialNumber}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '8px' }}>
                <span style={{ color: 'var(--dim)' }}>Tested Procedures:</span>
                <strong style={{ color: 'var(--lime)', fontFamily: 'ui-monospace, monospace' }}>
                  {ev.passedProcedures} / {ev.totalProcedures} Passed
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: 'var(--dim)' }}>Evaluator:</span>
                <span style={{ color: 'var(--muted)' }}>{ev.operatorName}</span>
              </div>
            </div>

            <div style={{ marginTop: 'auto', display: 'flex', gap: '10px' }}>
              <Link
                href={`/evaluations/${ev.id}/report`}
                className="button"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                Preview report <FileCheck2 style={{ width: '13px' }} />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
