'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  Check,
  FileCheck2,
  Printer,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { EvaluationRead } from '@/lib/types/domain'
import { getEvaluations } from '@/lib/api/services'
import { MOCK_EVALUATIONS } from '@/lib/mock-data'

export default function ReportsArchivePage() {
  const [evaluations, setEvaluations] = useState<EvaluationRead[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const list = await getEvaluations()
        if (list && list.length > 0) {
          setEvaluations(list)
        } else {
          // Fallback to mock evaluations
          setEvaluations(
            MOCK_EVALUATIONS.map((e) => ({
              id: e.id,
              evaluation_number: e.evaluationNumber,
              instrument_id: e.instrument.id,
              instrument_configuration_id: `cfg-${e.instrument.id}`,
              rule_version_id: e.ruleVersion,
              configuration_snapshot: {
                accuracy_class: e.instrument.accuracyClass,
                max_capacity: String(e.instrument.maxCapacity),
                min_capacity: String(e.instrument.minCapacity),
                verification_scale_interval: String(e.instrument.verificationScaleInterval),
                actual_scale_interval: String(e.instrument.actualScaleInterval),
                unit: e.instrument.unit,
                number_of_ranges: e.instrument.numberOfRanges,
                is_multiple_range: e.instrument.isMultipleRange,
                tare_type: e.instrument.tareType,
                is_electronic: true,
                has_zero_setting: true,
                snapshot_timestamp: e.createdAt,
                instrument_serial: e.instrument.serialNumber,
                manufacturer: e.instrument.manufacturer,
                model_name: e.instrument.modelName,
              },
              status: e.status as any,
              lab_name: e.labName,
              created_at: e.createdAt,
            }))
          )
        }
      } catch (err) {
        console.warn('Error loading evaluations for report archive:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = evaluations.filter((e) => {
    const q = searchQuery.toLowerCase()
    const snap = e.configuration_snapshot || {}
    return (
      e.evaluation_number.toLowerCase().includes(q) ||
      (snap.model_name && snap.model_name.toLowerCase().includes(q)) ||
      (snap.instrument_serial && snap.instrument_serial.toLowerCase().includes(q)) ||
      (snap.manufacturer && snap.manufacturer.toLowerCase().includes(q))
    )
  })

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

      {/* Search Input */}
      <div className="panel" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search style={{ width: '15px', color: 'var(--dim)' }} />
          <input
            type="text"
            placeholder="Search evaluation reports by model, evaluation number, or serial..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', background: 'transparent', border: 0, outline: 0, color: 'var(--ink)', fontSize: '12px' }}
          />
        </div>
      </div>

      {loading ? (
        <div className="panel" style={{ padding: '48px', textAlign: 'center' }}>
          <RefreshCw className="animate-spin" style={{ width: '24px', margin: '0 auto 12px', color: 'var(--lime)' }} />
          <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Loading evaluation archive...</p>
        </div>
      ) : (
        <div className="editorial-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
          {filtered.map((ev) => {
            const snap = ev.configuration_snapshot || {}
            return (
              <div key={ev.id} className="panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                  <div>
                    <span className="eyebrow lime-text">REPORT REF: {ev.evaluation_number}</span>
                    <h2 style={{ fontSize: '20px', margin: '6px 0 4px', color: 'var(--warm)' }}>
                      {snap.model_name || 'NAWI Model'}
                    </h2>
                    <span style={{ fontSize: '11px', color: 'var(--dim)', fontFamily: 'ui-monospace, monospace' }}>
                      Standard: {ev.rule_version_id || 'OIML R 76-1:2006'}
                    </span>
                  </div>
                  <Badge tone={ev.status === 'COMPLIANT' ? 'lime' : ev.status === 'NON_COMPLIANT' ? 'red' : 'amber'}>
                    {ev.status}
                  </Badge>
                </div>

                <p style={{ color: 'var(--muted)', fontSize: '12px', margin: '16px 0 20px', lineHeight: 1.5 }}>
                  {snap.manufacturer} · Class {snap.accuracy_class?.replace('_', ' ') || 'III'} ·{' '}
                  {snap.is_multiple_range ? `Multiple Range (${snap.ranges?.length || 2} ranges)` : 'Single Range'}
                </p>

                <div style={{ background: '#0b0e0c', borderRadius: '8px', padding: '14px', border: '1px solid var(--line)', marginBottom: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--dim)' }}>Instrument Serial:</span>
                    <strong style={{ color: 'var(--ink)', fontFamily: 'ui-monospace, monospace' }}>
                      {snap.instrument_serial || '—'}
                    </strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--dim)' }}>Capacity Limit:</span>
                    <strong style={{ color: 'var(--lime)', fontFamily: 'ui-monospace, monospace' }}>
                      Max {snap.max_capacity} {snap.unit}
                    </strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                    <span style={{ color: 'var(--dim)' }}>Laboratory:</span>
                    <span style={{ color: 'var(--muted)' }}>{ev.lab_name || 'Legal Metrology Lab'}</span>
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
            )
          })}
        </div>
      )}
    </div>
  )
}
