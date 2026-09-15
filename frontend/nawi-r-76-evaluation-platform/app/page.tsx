'use client'

import React from 'react'
import { HeroSection } from '@/components/overview/hero-section'
import { JourneySummary } from '@/components/overview/journey-summary'
import { ApplicabilityDemo } from '@/components/overview/applicability-demo'
import { TestPlanPreview } from '@/components/overview/test-plan-preview'
import { GuidedTestPreview } from '@/components/overview/guided-test-preview'
import { CalculationPreview } from '@/components/overview/calculation-preview'
import { EvidenceChainPreview } from '@/components/overview/evidence-chain-preview'
import { CtaSection } from '@/components/overview/cta-section'

export default function OverviewPage() {
  return (
    <main className="content" style={{ maxWidth: '1480px', margin: '0 auto', padding: '48px 42px 100px' }}>
      {/* 1. Hero */}
      <HeroSection />

      {/* 01—07 Sequential Pipeline Overview & Active Evaluation Highlight */}
      <JourneySummary />

      {/* 2. Instrument Configuration → Applicability demonstration */}
      <ApplicabilityDemo />

      {/* 3. Generated R-76 Test Plan preview */}
      <TestPlanPreview />

      {/* 4. Guided testing / test execution preview */}
      <GuidedTestPreview />

      {/* 5. Deterministic calculation + MPE preview */}
      <CalculationPreview />

      {/* 6. Evidence trace preview */}
      <EvidenceChainPreview />

      {/* 7. Technical report CTA */}
      <CtaSection />
    </main>
  )
}
