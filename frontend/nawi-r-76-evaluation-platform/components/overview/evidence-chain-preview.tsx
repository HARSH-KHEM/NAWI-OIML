'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Check, ChevronDown, FileCheck2, GitBranch } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

interface EvidenceNode {
  num: string
  title: string
  detail: string
  proof: string
}

const EVIDENCE_NODES: EvidenceNode[] = [
  {
    num: 'PASS',
    title: 'Compliance Decision',
    detail: 'All applicable R-76 clauses satisfied without violation.',
    proof: 'Decision: PASS · Margin: +0.008 kg inside MPE limit · Decided by Rule Engine',
  },
  {
    num: '01',
    title: 'Evaluation Criterion',
    detail: 'OIML R 76-1:2006 Table 6 MPE Tier: ±1.0 e (±0.010 kg).',
    proof: 'Condition: |Ec| ≤ MPE · Accuracy Class III · Load Range 500e < m ≤ 2000e',
  },
  {
    num: '02',
    title: 'Deterministic Calculation',
    detail: 'Corrected Error Ec = +0.002 kg via formula P = I + ½e - ΔL.',
    proof: 'I = 10.000 kg, e = 0.010 kg, ΔL = 0.003 kg, P = 10.002 kg, E0 = 0.000 kg',
  },
  {
    num: '03',
    title: 'Raw Observation Record',
    detail: 'Measurement recorded by certified laboratory operator.',
    proof: 'Load: 10.000 kg · Indication: 10.000 kg · Operator: Alex Morgan · Immutable',
  },
  {
    num: '04',
    title: 'Test Attempt Record',
    detail: 'Attempt 01 executed. No overwrite of historical loading data.',
    proof: 'Attempt #1 · Status: COMPLETED · Non-destructive audit history preserved',
  },
  {
    num: '05',
    title: 'Test Procedure Instance',
    detail: 'Clause A.4.4 · Weighing Performance Intrinsic Error Test.',
    proof: 'Sequence #10 · Scope: Instrument · Governing Clause: A.4.4',
  },
  {
    num: '06',
    title: 'Frozen Configuration Snapshot',
    detail: 'Immutable snapshot captured at evaluation initialization.',
    proof: 'Max: 30.000 kg, Min: 0.200 kg, e: 0.010 kg, Subtractive Tare, Electronic: true',
  },
  {
    num: '07',
    title: 'Standard Rule Version',
    detail: 'OIML R 76-1:2006 (E) · RuleVersion ID 2006-01 (Active).',
    proof: 'Deterministic AST hash: sha256:7f3b89e21... · Failsafe closed dispatch',
  },
]

export function EvidenceChainPreview() {
  const containerRef = useRef<HTMLElement | null>(null)
  const [openedNode, setOpenedNode] = useState<number | null>(0)

  useEffect(() => {
    if (!containerRef.current) return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 75%',
        },
        defaults: { ease: 'power3.out' },
      })

      tl.from('.evidence-head', {
        opacity: 0,
        y: 16,
        duration: 0.5,
      }).from(
        '.evidence-node',
        {
          opacity: 0,
          y: 20,
          stagger: 0.09, // Progressive sequential reveal of the 8-tier chain
          duration: 0.45,
          ease: 'power2.out',
        },
        '-=0.2'
      )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section className="overview-section" id="evidence-traceability" ref={containerRef}>
      <div className="section-overline">
        06 · Evidence Graph <span>FULL REGULATORY TRACEABILITY</span>
      </div>

      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div>
          <div className="eyebrow">
            <span>06</span>Every Decision Has An Unbroken Audit Trail
          </div>
          <h2 style={{ margin: '8px 0', fontSize: 'clamp(28px, 4vw, 48px)', letterSpacing: '-0.05em' }}>
            From final PASS back to the governing clause.
          </h2>
          <p>
            An explainable compliance chain. Auditors and judges can click any decision and inspect
            every intermediate calculation, raw observation, and the frozen configuration snapshot.
          </p>
        </div>
        <div className="header-actions">
          <Link href="/evaluations/EV-2026-001/evidence" className="button">
            Explore full graph <GitBranch />
          </Link>
        </div>
      </div>

      <div className="panel evidence-panel">
        <div className="evidence-head">
          <div className="decision-icon" aria-hidden="true">
            <FileCheck2 />
          </div>
          <div>
            <Badge tone="lime">Trace Verified & Immutable</Badge>
            <h2>EV-2026-001 · Unbroken Compliance Chain</h2>
            <p>Cryptographically linked record · Captured and sealed in audit store</p>
          </div>
        </div>

        <div className="evidence-chain" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          {EVIDENCE_NODES.map((node, i) => {
            const isOpen = openedNode === i
            return (
              <button
                type="button"
                className={`evidence-node ${isOpen ? 'opened' : ''}`}
                key={node.title}
                onClick={() => setOpenedNode(isOpen ? null : i)}
                aria-expanded={isOpen}
              >
                <div className="evidence-marker">
                  <span>{node.num === 'PASS' ? <Check /> : node.num}</span>
                  {i < EVIDENCE_NODES.length - 1 && <i aria-hidden="true" />}
                </div>
                <div className="evidence-copy">
                  <strong>{node.title}</strong>
                  <span>{node.detail}</span>
                  <small>
                    Verified Record <Check />
                  </small>
                  {isOpen && (
                    <div className="evidence-detail" role="region">
                      {node.proof}
                    </div>
                  )}
                </div>
                <ChevronDown className="evidence-chevron" aria-hidden="true" />
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
