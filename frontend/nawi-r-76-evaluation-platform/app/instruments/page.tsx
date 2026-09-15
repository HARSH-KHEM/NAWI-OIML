'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  Gauge,
  Plus,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { MOCK_INSTRUMENTS } from '@/lib/mock-data'

export default function InstrumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredInstruments = MOCK_INSTRUMENTS.filter((inst) => {
    return (
      inst.modelName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inst.manufacturer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inst.serialNumber.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>02</span>Instrument Registry
          </div>
          <h1>Weighing Instruments</h1>
          <p>
            Master catalog of Non-Automatic Weighing Instruments (NAWIs) registered for type evaluation.
            Each instrument configuration forms the authoritative input for rule applicability.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/new" className="button">
            <Plus /> Register instrument
          </Link>
        </div>
      </div>

      {/* Search Bar */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search style={{ width: '15px', color: 'var(--dim)' }} />
          <input
            type="text"
            placeholder="Search instruments by model, manufacturer, or serial number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', background: 'transparent', border: 0, outline: 0, color: 'var(--ink)', fontSize: '12px' }}
          />
        </div>
      </div>

      {/* Instruments Grid */}
      <div className="editorial-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {filteredInstruments.map((inst) => (
          <div key={inst.id} className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div className="instrument-symbol" style={{ width: '38px', height: '38px' }} aria-hidden="true">
                  <Gauge style={{ width: '18px' }} />
                </div>
                <div>
                  <h2 style={{ fontSize: '18px', margin: '0 0 4px', color: 'var(--warm)' }}>{inst.modelName}</h2>
                  <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                    SN: {inst.serialNumber}
                  </span>
                </div>
              </div>
              <Badge tone={inst.isSynthetic ? 'neutral' : 'lime'}>
                {inst.isSynthetic ? 'Synthetic Fixture' : 'Active'}
              </Badge>
            </div>

            <p style={{ color: 'var(--muted)', fontSize: '12px', margin: '14px 0 16px' }}>
              {inst.manufacturer} · Family: {inst.instrumentFamily}
            </p>

            {/* Metrological Specs Table */}
            <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '14px', border: '1px solid var(--line)', marginBottom: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div>
                  <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block' }}>CLASS</span>
                  <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                    {inst.accuracyClass.replace('_', ' ')}
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block' }}>CAPACITY (MAX)</span>
                  <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                    {inst.maxCapacity} {inst.unit}
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block' }}>SCALE INTERVAL (E)</span>
                  <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                    {inst.verificationScaleInterval} {inst.unit}
                  </strong>
                </div>
              </div>

              <div style={{ height: '1px', background: 'var(--line)', margin: '10px 0' }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--dim)' }}>
                <span>Ranges: {inst.isMultipleRange ? 'Multiple (2 Ranges)' : 'Single Range'}</span>
                <span>Supports: {inst.loadReceptor.supportCount} Points</span>
                <span>Tare: {inst.tareType}</span>
              </div>
            </div>

            <div style={{ marginTop: 'auto', display: 'flex', gap: '10px' }}>
              <Link href="/evaluations/new" className="button" style={{ flex: 1, justifyContent: 'center' }}>
                Launch evaluation <ArrowRight />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
