'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  Check,
  CircleHelp,
  ClipboardCheck,
  Search,
  TestTube2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { CANONICAL_PROCEDURES } from '@/lib/mock-data'

export default function TestPlansPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeWhy, setActiveWhy] = useState<string | null>(null)

  const filteredProcedures = CANONICAL_PROCEDURES.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.r76Ref.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>03</span>Standard Test Procedures Catalog
          </div>
          <h1>OIML R-76 Test Procedures</h1>
          <p>
            Master library of non-automatic weighing instrument test procedures according to OIML R 76-1:2006 (E).
            The Applicability Engine dynamically selects procedures from this catalog based on instrument configuration.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/new" className="button">
            Configure evaluation <ArrowRight />
          </Link>
        </div>
      </div>

      {/* Search Input */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search style={{ width: '15px', color: 'var(--dim)' }} />
          <input
            type="text"
            placeholder="Search test procedures by name, code, or R-76 clause reference..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', background: 'transparent', border: 0, outline: 0, color: 'var(--ink)', fontSize: '12px' }}
          />
        </div>
      </div>

      {/* Procedures Table */}
      <div className="panel" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 1.5fr 1fr 1fr 1fr auto', padding: '14px 24px', borderBottom: '1px solid var(--line)', color: 'var(--dim)', font: '9px ui-monospace, SFMono-Regular, monospace', letterSpacing: '0.08em' }}>
          <span>CLAUSE</span>
          <span>PROCEDURE NAME</span>
          <span>SCOPE</span>
          <span>STATUS</span>
          <span>APPLICABILITY TRIGGER</span>
          <span style={{ textAlign: 'right' }}>INFO</span>
        </div>

        {filteredProcedures.map((proc) => {
          const isWhyOpen = activeWhy === proc.id

          return (
            <div
              key={proc.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '80px 1.5fr 1fr 1fr 1fr auto',
                alignItems: 'center',
                padding: '20px 24px',
                borderBottom: '1px solid var(--line)',
                gap: '12px',
                position: 'relative',
              }}
            >
              <div>
                <strong style={{ fontFamily: 'ui-monospace, monospace', fontSize: '12px', color: 'var(--lime)' }}>
                  {proc.r76Ref}
                </strong>
              </div>

              <div>
                <strong style={{ fontSize: '13px', color: 'var(--warm)', display: 'block' }}>
                  {proc.name}
                </strong>
                <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                  {proc.code}
                </span>
              </div>

              <div>
                <Badge tone={proc.scope === 'RANGE' ? 'lime' : 'neutral'}>
                  {proc.scope}
                </Badge>
              </div>

              <div>
                <Badge tone={proc.status === 'IMPLEMENTED' ? 'lime' : proc.status === 'PARTIAL' ? 'amber' : 'neutral'}>
                  {proc.status}
                </Badge>
              </div>

              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', maxWidth: '320px' }}>
                  {proc.description}
                </span>
              </div>

              <div style={{ textAlign: 'right' }}>
                <button
                  type="button"
                  className="why"
                  onClick={() => setActiveWhy(!isWhyOpen ? proc.id : null)}
                  aria-label={`Why is ${proc.name} applicable?`}
                  title="Inspect R-76 applicability rule"
                >
                  <CircleHelp style={{ width: '16px' }} />
                </button>
              </div>

              {isWhyOpen && (
                <div
                  className="why-detail"
                  style={{
                    gridColumn: '1 / -1',
                    position: 'static',
                    margin: '10px 0 4px',
                  }}
                >
                  <span>AUTHORITATIVE R-76 APPLICABILITY RULE</span>
                  <p>
                    <strong>Clause {proc.r76Ref}:</strong> {proc.whyApplicable}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
