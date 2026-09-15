'use client'

import React, { useEffect, useRef } from 'react'
import Link from 'next/link'
import { ArrowDownRight, ArrowRight } from 'lucide-react'
import gsap from 'gsap'

export function HeroSection() {
  const containerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })

      tl.from('.hero-kicker', {
        opacity: 0,
        y: 12,
        duration: 0.6,
      })
        .from(
          '.hero h1',
          {
            opacity: 0,
            y: 24,
            duration: 0.8,
          },
          '-=0.3'
        )
        .from(
          '.hero p',
          {
            opacity: 0,
            y: 16,
            duration: 0.6,
          },
          '-=0.4'
        )
        .from(
          '.hero-actions .button',
          {
            opacity: 0,
            y: 12,
            stagger: 0.1,
            duration: 0.5,
          },
          '-=0.3'
        )
        .from(
          '.hero-meta span',
          {
            opacity: 0,
            y: 10,
            stagger: 0.08,
            duration: 0.4,
          },
          '-=0.2'
        )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section className="hero" ref={containerRef}>
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
