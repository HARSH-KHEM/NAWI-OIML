'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  ChevronRight,
  Filter,
  Gauge,
  Layers,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { InstrumentRead } from '@/lib/types/domain'
import { getInstruments } from '@/lib/api/services'

export default function InstrumentsPage() {
  const [instruments, setInstruments] = useState<InstrumentRead[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [classFilter, setClassFilter] = useState<string>('ALL')

  useEffect(() => {
    async function load() {
      setLoading(true)
      const data = await getInstruments()
      setInstruments(data)
      setLoading(false)
    }
    load()
  }, [])

  const filteredInstruments = instruments.filter((inst) => {
    const activeConfig = inst.configurations?.[0]
    const matchesSearch =
      inst.model_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inst.manufacturer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inst.serial_number.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesClass =
      classFilter === 'ALL' ||
      (activeConfig && activeConfig.accuracy_class === classFilter)

    return matchesSearch && matchesClass
  })

  return (
    <div className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '42px 42px 90px' }}>
      <div className="page-header">
        <div>
          <div className="eyebrow">
            <span>02</span>Instrument Registry
          </div>
          <h1>Weighing Instruments Catalog</h1>
          <p>
            Master metrological registry of Non-Automatic Weighing Instruments (NAWIs).
            Each registered instrument maintains versioned metrological specifications that deterministically
            govern OIML R 76 test applicability.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/instruments/new" className="button">
            <Plus /> Register new instrument
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '280px' }}>
            <Search style={{ width: '15px', color: 'var(--dim)' }} />
            <input
              type="text"
              placeholder="Search instruments by model, manufacturer, or serial number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', background: 'transparent', border: 0, outline: 0, color: 'var(--ink)', fontSize: '12px' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter style={{ width: '13px', color: 'var(--dim)' }} />
            <span style={{ fontSize: '11px', color: 'var(--dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Class:
            </span>
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              style={{
                background: '#0d110f',
                border: '1px solid var(--line)',
                borderRadius: '6px',
                color: 'var(--ink)',
                fontSize: '11px',
                padding: '6px 10px',
                outline: 0,
              }}
            >
              <option value="ALL">All Accuracy Classes</option>
              <option value="CLASS_I">Class I (Special)</option>
              <option value="CLASS_II">Class II (High)</option>
              <option value="CLASS_III">Class III (Medium)</option>
              <option value="CLASS_IIII">Class IIII (Ordinary)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Catalog Grid */}
      {loading ? (
        <div className="panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <RefreshCw className="animate-spin" style={{ width: '24px', margin: '0 auto 12px', color: 'var(--lime)' }} />
          <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Loading instrument registry from backend...</p>
        </div>
      ) : filteredInstruments.length === 0 ? (
        <div className="panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <p style={{ color: 'var(--muted)', fontSize: '13px', marginBottom: '16px' }}>
            No instruments match the current search filters.
          </p>
          <Link href="/instruments/new" className="button" style={{ display: 'inline-flex' }}>
            <Plus /> Register first instrument
          </Link>
        </div>
      ) : (
        <div className="editorial-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '20px' }}>
          {filteredInstruments.map((inst) => {
            const config = inst.configurations?.[0]
            const isMulti = config?.is_multiple_range ?? false
            const supportCount = config?.extra_capabilities?.load_receptor?.support_count ?? 4

            return (
              <div
                key={inst.id}
                className="panel"
                style={{ padding: '24px', display: 'flex', flexDirection: 'column', position: 'relative' }}
              >
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="instrument-symbol" style={{ width: '40px', height: '40px' }} aria-hidden="true">
                      <Gauge style={{ width: '18px' }} />
                    </div>
                    <div>
                      <Link
                        href={`/instruments/${inst.id}`}
                        style={{ textDecoration: 'none', color: 'inherit' }}
                      >
                        <h2 style={{ fontSize: '18px', margin: '0 0 4px', color: 'var(--warm)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {inst.model_name}
                          <ChevronRight style={{ width: '14px', color: 'var(--dim)' }} />
                        </h2>
                      </Link>
                      <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                        SN: {inst.serial_number}
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <Badge tone={inst.is_synthetic ? 'neutral' : 'lime'}>
                      {inst.is_synthetic ? 'Synthetic Fixture' : 'Physical'}
                    </Badge>
                    <Badge tone="neutral">{inst.status}</Badge>
                  </div>
                </div>

                <p style={{ color: 'var(--muted)', fontSize: '12px', margin: '14px 0 16px' }}>
                  {inst.manufacturer} · Family: {inst.instrument_family}
                </p>

                {/* Metrological Specifications Card */}
                {config ? (
                  <div
                    style={{
                      background: '#0b0e0c',
                      borderRadius: '8px',
                      padding: '14px',
                      border: '1px solid var(--line)',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                      <div>
                        <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block', textTransform: 'uppercase' }}>
                          Class
                        </span>
                        <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                          {config.accuracy_class.replace('_', ' ')}
                        </strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block', textTransform: 'uppercase' }}>
                          Max Capacity
                        </span>
                        <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                          {config.max_capacity} {config.unit}
                        </strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block', textTransform: 'uppercase' }}>
                          Scale Interval (e)
                        </span>
                        <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                          {config.verification_scale_interval} {config.unit}
                        </strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '9px', color: 'var(--dim)', display: 'block', textTransform: 'uppercase' }}>
                          Resolution (d)
                        </span>
                        <strong style={{ fontSize: '12px', color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                          {config.actual_scale_interval} {config.unit}
                        </strong>
                      </div>
                    </div>

                    <div style={{ height: '1px', background: 'var(--line)', margin: '10px 0' }} />

                    {/* Multi-Range Breakdown or Single Range details */}
                    {isMulti && config.ranges && config.ranges.length > 0 ? (
                      <div style={{ marginBottom: '8px', padding: '6px 8px', background: 'rgba(182, 237, 78, 0.05)', borderRadius: '4px', border: '1px solid rgba(182, 237, 78, 0.15)' }}>
                        <div style={{ fontSize: '10px', color: 'var(--lime)', fontWeight: 600, marginBottom: '4px' }}>
                          Multiple Range ({config.ranges.length} partial ranges):
                        </div>
                        <div style={{ display: 'flex', gap: '12px', fontSize: '10px', color: 'var(--dim)' }}>
                          {config.ranges.map((r) => (
                            <span key={r.range_index} style={{ fontFamily: 'ui-monospace, monospace' }}>
                              W{r.range_index}: {r.min_capacity}–{r.max_capacity} {r.unit} (e={r.verification_scale_interval})
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--dim)', flexWrap: 'wrap', gap: '6px' }}>
                      <span>Mode: {isMulti ? 'Multiple Range' : 'Single Range'}</span>
                      <span>Supports: {supportCount} Points</span>
                      <span>Tare: {config.tare_type}</span>
                      <span>Zero: {config.has_zero_setting ? 'Automatic' : 'Manual'}</span>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      background: '#0b0e0c',
                      borderRadius: '8px',
                      padding: '14px',
                      border: '1px dashed var(--line)',
                      marginBottom: '20px',
                      color: 'var(--dim)',
                      fontSize: '11px',
                    }}
                  >
                    No active metrological configuration attached yet.
                  </div>
                )}

                {/* Card Action Buttons */}
                <div style={{ marginTop: 'auto', display: 'flex', gap: '10px' }}>
                  <Link
                    href={`/instruments/${inst.id}`}
                    className="button button-outline"
                    style={{ flex: 1, justifyContent: 'center', fontSize: '11px' }}
                  >
                    <SlidersHorizontal style={{ width: '13px' }} /> Details
                  </Link>
                  <Link
                    href={`/evaluations/new?instrumentId=${inst.id}`}
                    className="button"
                    style={{ flex: 1.3, justifyContent: 'center', fontSize: '11px' }}
                  >
                    Launch evaluation <ArrowRight style={{ width: '13px' }} />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
