import React from 'react'
import Link from 'next/link'
import { Check } from 'lucide-react'

export interface PipelineProps {
  current: number // 0-based index: 0=Configure, 1=Applicability, 2=Test Plan, 3=Guided Test, 4=Calculate, 5=Evidence, 6=Report
  evaluationId?: string
}

export const PIPELINE_STEPS = [
  { label: 'Configure', path: 'configuration' },
  { label: 'Applicability', path: 'plan' },
  { label: 'Test Plan', path: 'plan' },
  { label: 'Guided Test', path: 'tests' },
  { label: 'Calculate', path: 'compliance' },
  { label: 'Evidence', path: 'evidence' },
  { label: 'Report', path: 'report' },
] as const

export function Pipeline({ current, evaluationId }: PipelineProps) {
  return (
    <div className="pipeline" role="navigation" aria-label="Evaluation Workflow Stages">
      {PIPELINE_STEPS.map((step, i) => {
        const isComplete = i < current
        const isCurrent = i === current
        const content = (
          <div
            className={`pipe-step ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''}`}
            key={step.label}
          >
            <span>
              {isComplete ? <Check aria-hidden="true" /> : String(i + 1).padStart(2, '0')}
            </span>
            <strong>{step.label}</strong>
            {i < PIPELINE_STEPS.length - 1 && <i aria-hidden="true" />}
          </div>
        )

        if (evaluationId && isComplete) {
          const href = `/evaluations/${evaluationId}/${step.path}`
          return (
            <Link key={step.label} href={href} className="pipe-step-link">
              {content}
            </Link>
          )
        }

        return <React.Fragment key={step.label}>{content}</React.Fragment>
      })}
    </div>
  )
}
