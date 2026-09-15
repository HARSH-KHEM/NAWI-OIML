'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  ClipboardCheck,
  FileCheck2,
  Filter,
  Plus,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function EvaluationsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLIANT' | 'IN_PROGRESS'>('ALL')

  const filteredEvaluations = MOCK_EVALUATIONS.filter((ev) => {
    const matchesQuery =
      ev.evaluationNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.instrument.modelName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.instrument.serialNumber.toLowerCase().includes(searchQuery.toLowerCase())

    if (statusFilter === 'ALL') return matchesQuery
    return matchesQuery && ev.status === statusFilter
  })

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>01</span>Legal Metrology Evaluation Repository
          </div>
          <h1>Type Evaluations</h1>
          <p>
            Browse, search, and audit all type evaluations conducted under OIML R 76-1:2006.
            Each evaluation locks an immutable configuration snapshot and traceable calculations.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/new" className="button">
            <Plus /> New evaluation
          </Link>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="editorial-grid" style={{ marginBottom: '32px' }}>
        <div className="evaluation-card" style={{ minHeight: 'auto', padding: '20px' }}>
          <div className="card-topline">
            <span>Total Evaluations</span>
            <ClipboardCheck style={{ color: 'var(--lime)', width: '16px' }} />
          </div>
          <strong className="big-number" style={{ margin: '18px 0 6px', fontSize: '38px' }}>
            02
          </strong>
          <p>Registered in audit store</p>
        </div>

        <div className="evaluation-card dark" style={{ minHeight: 'auto', padding: '20px' }}>
          <div className="card-topline">
            <span>Compliant Decisions</span>
            <ShieldCheck style={{ color: 'var(--lime)', width: '16px' }} />
          </div>
          <strong className="decision" style={{ margin: '18px 0 6px', fontSize: '28px' }}>
            01 PASS
          </strong>
          <p>Full Table 6 compliance</p>
        </div>

        <div className="evaluation-card outlined" style={{ minHeight: 'auto', padding: '20px' }}>
          <div className="card-topline">
            <span>In Progress</span>
            <SlidersHorizontal style={{ color: 'var(--amber)', width: '16px' }} />
          </div>
          <strong className="big-number" style={{ margin: '18px 0 6px', fontSize: '38px', color: 'var(--amber)' }}>
            01 ACTIVE
          </strong>
          <p>Multi-range partial testing</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '240px' }}>
          <Search style={{ width: '15px', color: 'var(--dim)' }} />
          <input
            type="text"
            placeholder="Filter by evaluation number, model name, or serial number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', background: 'transparent', border: 0, outline: 0, color: 'var(--ink)', fontSize: '12px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter style={{ width: '13px', color: 'var(--dim)' }} />
          <span style={{ fontSize: '10px', color: 'var(--dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Status:</span>
          <div className="segmented">
            <button
              className={statusFilter === 'ALL' ? 'selected' : ''}
              onClick={() => setStatusFilter('ALL')}
            >
              All
            </button>
            <button
              className={statusFilter === 'COMPLIANT' ? 'selected' : ''}
              onClick={() => setStatusFilter('COMPLIANT')}
            >
              Compliant
            </button>
            <button
              className={statusFilter === 'IN_PROGRESS' ? 'selected' : ''}
              onClick={() => setStatusFilter('IN_PROGRESS')}
            >
              In Progress
            </button>
          </div>
        </div>
      </div>

      {/* Evaluations Table / Cards */}
      <div className="panel" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.6fr 1fr 1fr 1fr auto', padding: '14px 24px', borderBottom: '1px solid var(--line)', color: 'var(--dim)', font: '9px ui-monospace, SFMono-Regular, monospace', letterSpacing: '0.08em' }}>
          <span>EVALUATION ID</span>
          <span>INSTRUMENT MODEL</span>
          <span>CONFIGURATION</span>
          <span>STATUS</span>
          <span>PROCEDURES</span>
          <span style={{ textAlign: 'right' }}>ACTION</span>
        </div>

        {filteredEvaluations.map((ev) => (
          <div
            key={ev.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '1.2fr 1.6fr 1fr 1fr 1fr auto',
              alignItems: 'center',
              padding: '20px 24px',
              borderBottom: '1px solid var(--line)',
              gap: '12px',
              transition: 'background 0.18s',
            }}
          >
            <div>
              <strong style={{ fontFamily: 'ui-monospace, monospace', fontSize: '13px', color: 'var(--warm)', display: 'block' }}>
                {ev.evaluationNumber}
              </strong>
              <small style={{ color: 'var(--dim)', fontSize: '9px', fontFamily: 'ui-monospace, monospace' }}>
                {new Date(ev.createdAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
              </small>
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <strong style={{ fontSize: '13px', color: 'var(--ink)' }}>{ev.instrument.modelName}</strong>
                {ev.instrument.isSynthetic && <Badge tone="neutral">Synthetic</Badge>}
              </div>
              <span style={{ color: 'var(--muted)', fontSize: '11px', display: 'block', marginTop: '2px' }}>
                SN: {ev.instrument.serialNumber} · {ev.instrument.accuracyClass.replace('_', ' ')}
              </span>
            </div>

            <div>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '11px', color: 'var(--muted)' }}>
                Max {ev.instrument.maxCapacity} {ev.instrument.unit}
              </span>
              <span style={{ display: 'block', color: 'var(--dim)', fontSize: '10px' }}>
                {ev.instrument.isMultipleRange ? 'Multiple Range (2 ranges)' : 'Single Range'}
              </span>
            </div>

            <div>
              <Badge tone={ev.status === 'COMPLIANT' ? 'lime' : 'amber'}>
                {ev.status === 'COMPLIANT' ? 'COMPLIANT' : 'IN PROGRESS'}
              </Badge>
            </div>

            <div>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '12px', color: 'var(--warm)' }}>
                {ev.passedProcedures} / {ev.totalProcedures} passed
              </span>
              <div style={{ height: '3px', background: 'var(--line)', marginTop: '5px', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(ev.passedProcedures / ev.totalProcedures) * 100}%`, background: ev.status === 'COMPLIANT' ? 'var(--lime)' : 'var(--amber)' }} />
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <Link href={`/evaluations/${ev.id}`} className="button button-secondary" style={{ padding: '8px 14px', fontSize: '11px' }}>
                Open <ArrowRight style={{ width: '12px' }} />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
