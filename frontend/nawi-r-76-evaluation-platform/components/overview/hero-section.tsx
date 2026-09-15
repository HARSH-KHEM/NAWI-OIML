'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowDownRight, ArrowRight, ShieldCheck } from 'lucide-react'

export function HeroSection() {
  return (
    <section className="hero">
      <div className="hero-kicker">
        <span className="live-dot" /> Configuration-Driven Legal Metrology Engine
      </div>
      <h1>
        R-76
        <br />
        <em>evaluation engine.</em>
      </h1>
      <p>
        From instrument configuration
        <br />
        to executable, auditable compliance.
      </p>

      <div className="hero-actions">
        <Link href="/evaluations/new" className="button">
          Start evaluation <ArrowRight />
        </Link>
        <Link href="/instruments" className="button button-secondary">
          View instruments <ArrowDownRight />
        </Link>
      </div>

      <div className="hero-meta">
        <span>OIML R 76-1:2006 STANDARD</span>
        <span>RULE VERSION / 2006-01</span>
        <span>EXECUTION / DETERMINISTIC DECIMAL</span>
        <span>EVIDENCE / IMMUTABLE TRACE</span>
      </div>
    </section>
  )
}
