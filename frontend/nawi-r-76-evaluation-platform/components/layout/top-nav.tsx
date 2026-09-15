'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Menu, Search, X, Zap } from 'lucide-react'

export function TopNav() {
  const pathname = usePathname()
  const [searchOpen, setSearchOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Global CMD+K shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearchOpen((prev) => !prev)
      } else if (e.key === 'Escape') {
        setSearchOpen(false)
        setMobileMenuOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const navLinks = [
    { href: '/', label: 'Overview' },
    { href: '/evaluations', label: 'Evaluations' },
    { href: '/instruments', label: 'Instruments' },
    { href: '/test-plans', label: 'Test Plans' },
    { href: '/reports', label: 'Reports' },
  ]

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  return (
    <>
      <header className="site-header">
        <div className="site-header-inner">
          {/* Mobile hamburger */}
          <button
            className="mobile-toggle"
            aria-label={mobileMenuOpen ? 'Close navigation' : 'Open navigation'}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>

          {/* Wordmark */}
          <Link href="/" className="wordmark-link" aria-label="METRA Home">
            <div className="wordmark">
              <span className="wordmark-mark">
                <Zap />
              </span>
              <span>
                METRA
                <small>R-76 / EVALUATION ENGINE</small>
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="site-nav" aria-label="Main Navigation">
            {navLinks.map((link) => {
              const active = isActive(link.href)
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`site-nav-link ${active ? 'active' : ''}`}
                >
                  {link.label}
                  {link.href === '/evaluations' && <span className="nav-pulse-dot" />}
                </Link>
              )
            })}
          </nav>

          {/* Right Header Actions */}
          <div className="header-actions">
            <button
              className="search-trigger"
              onClick={() => setSearchOpen(true)}
              aria-label="Open global search"
            >
              <Search />
              <span>Search</span>
              <kbd>⌘ K</kbd>
            </button>

            <div className="rule-version-pill" title="Active Standard Version">
              <span className="pill-dot" />
              <span>R-76-1:2006</span>
            </div>

            <div
              className="avatar avatar-top"
              title="Alex Morgan · Lead Metrological Engineer"
              aria-label="Alex Morgan"
            >
              AM
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav className="mobile-nav-drawer" aria-label="Mobile Navigation">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`mobile-nav-link ${isActive(link.href) ? 'active' : ''}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        )}
      </header>

      {/* Search Modal Overlay */}
      {searchOpen && (
        <div className="overlay" onClick={() => setSearchOpen(false)}>
          <div className="command" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            <div className="command-input">
              <Search />
              <input
                autoFocus
                placeholder="Search instruments, evaluations, test clauses, reports..."
                aria-label="Quick search query"
              />
              <kbd onClick={() => setSearchOpen(false)}>ESC</kbd>
            </div>
            <div className="command-results">
              <Link
                href="/evaluations/EV-2026-001"
                className="command-item"
                onClick={() => setSearchOpen(false)}
              >
                <span>
                  <strong>EV-2026-001 · ABC-300 Bench Scale</strong>
                  <small>Active Evaluation · Single Range Class III · R-76-1:2006</small>
                </span>
                <ChevronRight />
              </Link>
              <Link
                href="/instruments"
                className="command-item"
                onClick={() => setSearchOpen(false)}
              >
                <span>
                  <strong>SYNTH-DEMO-NAWI-001</strong>
                  <small>Synthetic Instrument Catalog · Max 30 kg · e 10 g</small>
                </span>
                <ChevronRight />
              </Link>
              <Link
                href="/evaluations/EV-2026-001/evidence"
                className="command-item"
                onClick={() => setSearchOpen(false)}
              >
                <span>
                  <strong>Evidence Traceability Graph</strong>
                  <small>Compliance Chain · Clause A.4.4 Intrinsic Error</small>
                </span>
                <ChevronRight />
              </Link>
              <Link
                href="/test-plans"
                className="command-item"
                onClick={() => setSearchOpen(false)}
              >
                <span>
                  <strong>OIML R 76-1:2006 Standard Test Catalog</strong>
                  <small>10 Core Procedures · Weighing, Eccentricity, Repeatability</small>
                </span>
                <ChevronRight />
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
