/**
 * Realistic synthetic laboratory data fixtures matching backend seed models.
 * Authoritative standard: OIML R 76-1:2006 (E).
 * All test instruments are flagged with is_synthetic: true.
 */

export interface TestProcedureDefinition {
  id: string
  code: string
  name: string
  r76Ref: string
  description: string
  scope: 'INSTRUMENT' | 'RANGE'
  status: 'IMPLEMENTED' | 'PARTIAL' | 'APPLICABILITY_ONLY'
  applicableToSingleRange: boolean
  applicableToMultipleRange: boolean
  whyApplicable: string
}

export const CANONICAL_PROCEDURES: TestProcedureDefinition[] = [
  {
    id: 'PROC-01',
    code: 'WEIGHING_PERFORMANCE',
    name: 'Weighing Performance',
    r76Ref: 'A.4.4',
    description: 'Determine intrinsic error across minimum 10 ascending and descending test loads.',
    scope: 'INSTRUMENT',
    status: 'IMPLEMENTED',
    applicableToSingleRange: true,
    applicableToMultipleRange: false,
    whyApplicable: 'Mandatory primary error evaluation test under OIML R 76-1:2006 clause A.4.4 for single-range instruments.',
  },
  {
    id: 'PROC-01-R1',
    code: 'WEIGHING_PERFORMANCE_RANGE_1',
    name: 'Weighing Performance — Range 1',
    r76Ref: 'A.4.4.4',
    description: 'Determine intrinsic error across partial weighing range 1 (Max₁ = 15 kg, e₁ = 5 g).',
    scope: 'RANGE',
    status: 'IMPLEMENTED',
    applicableToSingleRange: false,
    applicableToMultipleRange: true,
    whyApplicable: 'Multiple range instruments require separate weighing performance evaluation for each partial weighing range under clause A.4.4.4.',
  },
  {
    id: 'PROC-01-R2',
    code: 'WEIGHING_PERFORMANCE_RANGE_2',
    name: 'Weighing Performance — Range 2',
    r76Ref: 'A.4.4.4',
    description: 'Determine intrinsic error across partial weighing range 2 (Max₂ = 30 kg, e₂ = 10 g).',
    scope: 'RANGE',
    status: 'IMPLEMENTED',
    applicableToSingleRange: false,
    applicableToMultipleRange: true,
    whyApplicable: 'Mandatory verification across partial weighing range 2 up to instrument total capacity.',
  },
  {
    id: 'PROC-02',
    code: 'ECCENTRICITY',
    name: 'Eccentric Loading Test',
    r76Ref: 'A.4.7',
    description: 'Evaluate indication error across 4 quarter-segments of load receptor (Clause A.4.7.1).',
    scope: 'INSTRUMENT',
    status: 'IMPLEMENTED',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Mandatory test with test load L = 1/3 Max placed at quarters 1 through 4 under clause A.4.7.',
  },
  {
    id: 'PROC-03',
    code: 'REPEATABILITY',
    name: 'Repeatability Test',
    r76Ref: 'A.4.10',
    description: 'Execute dual-series loadings at ~50% Max (Series A) and ~100% Max (Series B).',
    scope: 'INSTRUMENT',
    status: 'IMPLEMENTED',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Difference between max and min indications under repeated loading must not exceed Table 6 MPE.',
  },
  {
    id: 'PROC-04',
    code: 'TARE',
    name: 'Tare Balancing & Weighing',
    r76Ref: 'A.4.6',
    description: 'Verify accuracy of subtractive tare weighing and preset tare device.',
    scope: 'INSTRUMENT',
    status: 'PARTIAL',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Applicable because instrument is configured with subtractive tare mechanism under clause A.4.6.',
  },
  {
    id: 'PROC-05',
    code: 'ZERO_SETTING',
    name: 'Zero-Setting & Zero-Tracking',
    r76Ref: 'A.4.2',
    description: 'Determine zero-setting range and residual zero-setting accuracy.',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Applicable because instrument is configured with automatic/semi-automatic zero-setting under clause A.4.2.',
  },
  {
    id: 'PROC-06',
    code: 'CREEP',
    name: 'Creep Test',
    r76Ref: '3.9.4.1',
    description: 'Monitor indication variation under full load held for 30 minutes.',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Mandatory for Class III instruments under OIML R 76-1:2006 clause 3.9.4.1.',
  },
  {
    id: 'PROC-07',
    code: 'TEMPERATURE',
    name: 'Static Temperatures Test',
    r76Ref: 'A.5.3.1',
    description: 'Evaluate temperature coefficient of zero and span at +20°C, -10°C, and +40°C.',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Standard climatic influence factor evaluation under clause A.5.3.1.',
  },
  {
    id: 'PROC-08',
    code: 'VOLTAGE_VARIATION',
    name: 'Voltage Variations Test',
    r76Ref: 'A.5.4',
    description: 'Evaluate stability under mains supply voltage limits (-15% to +10%).',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Applicable because instrument is electronic with AC mains supply under clause A.5.4.',
  },
  {
    id: 'PROC-09',
    code: 'WARM_UP',
    name: 'Warm-up Test',
    r76Ref: 'A.5.2',
    description: 'Verify error immediately after power-up through thermal stabilization.',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Applicable to electronic instruments with mains power under clause A.5.2.',
  },
  {
    id: 'PROC-10',
    code: 'ENDURANCE',
    name: 'Endurance Test',
    r76Ref: '3.9.4.3',
    description: 'Repetitive loading up to 100,000 cycles for instruments with Max <= 100 kg.',
    scope: 'INSTRUMENT',
    status: 'APPLICABILITY_ONLY',
    applicableToSingleRange: true,
    applicableToMultipleRange: true,
    whyApplicable: 'Clause 3.9.4.3 mandates endurance testing for Class III instruments with capacity Max <= 100 kg.',
  },
]

export interface MockInstrument {
  id: string
  manufacturer: string
  modelName: string
  instrumentFamily: string
  serialNumber: string
  status: 'ACTIVE' | 'DRAFT' | 'RETIRED'
  isSynthetic: boolean
  accuracyClass: 'CLASS_I' | 'CLASS_II' | 'CLASS_III' | 'CLASS_IIII'
  maxCapacity: number
  minCapacity: number
  verificationScaleInterval: number
  actualScaleInterval: number
  unit: string
  isMultipleRange: boolean
  numberOfRanges: number
  tareType: 'SUBTRACTIVE' | 'ADDITIVE' | 'NONE'
  isElectronic: boolean
  hasZeroSetting: boolean
  loadReceptor: {
    supportCount: number
    specialReceptor: boolean
    rollingLoad: boolean
  }
}

export const MOCK_INSTRUMENTS: MockInstrument[] = [
  {
    id: 'inst-001',
    manufacturer: '[SYNTHETIC] Global Bench Metrology Systems',
    modelName: 'ABC-300 Bench Scale',
    instrumentFamily: 'NAWI',
    serialNumber: 'SYNTH-DEMO-NAWI-001-SN',
    status: 'ACTIVE',
    isSynthetic: true,
    accuracyClass: 'CLASS_III',
    maxCapacity: 30.0,
    minCapacity: 0.2,
    verificationScaleInterval: 0.01,
    actualScaleInterval: 0.01,
    unit: 'kg',
    isMultipleRange: false,
    numberOfRanges: 1,
    tareType: 'SUBTRACTIVE',
    isElectronic: true,
    hasZeroSetting: true,
    loadReceptor: {
      supportCount: 4,
      specialReceptor: false,
      rollingLoad: false,
    },
  },
  {
    id: 'inst-002',
    manufacturer: '[SYNTHETIC] Global Bench Metrology Systems',
    modelName: 'MR-1530 Multi-Range Retail Scale',
    instrumentFamily: 'NAWI',
    serialNumber: 'SYNTH-DEMO-MULTI-002-SN',
    status: 'ACTIVE',
    isSynthetic: true,
    accuracyClass: 'CLASS_III',
    maxCapacity: 30.0,
    minCapacity: 0.2,
    verificationScaleInterval: 0.01,
    actualScaleInterval: 0.01,
    unit: 'kg',
    isMultipleRange: true,
    numberOfRanges: 2,
    tareType: 'SUBTRACTIVE',
    isElectronic: true,
    hasZeroSetting: true,
    loadReceptor: {
      supportCount: 4,
      specialReceptor: false,
      rollingLoad: false,
    },
  },
]

export interface MockEvaluation {
  id: string
  evaluationNumber: string
  instrument: MockInstrument
  ruleVersion: string
  status: 'IN_PROGRESS' | 'COMPLIANT' | 'NON_COMPLIANT'
  createdAt: string
  updatedAt: string
  labName: string
  operatorName: string
  totalProcedures: number
  passedProcedures: number
  summary: string
}

export const MOCK_EVALUATIONS: MockEvaluation[] = [
  {
    id: 'EV-2026-001',
    evaluationNumber: 'EV-2026-001',
    instrument: MOCK_INSTRUMENTS[0],
    ruleVersion: 'OIML R 76-1:2006',
    status: 'COMPLIANT',
    createdAt: '2026-09-14T09:30:00Z',
    updatedAt: '2026-09-14T11:45:00Z',
    labName: 'National Type Evaluation Laboratory (Synthetic)',
    operatorName: 'Alex Morgan · Lead Metrologist',
    totalProcedures: 9,
    passedProcedures: 9,
    summary: 'Single-range Class III instrument fully compliant with OIML R 76-1:2006 metrological requirements.',
  },
  {
    id: 'EV-2026-002',
    evaluationNumber: 'EV-2026-002',
    instrument: MOCK_INSTRUMENTS[1],
    ruleVersion: 'OIML R 76-1:2006',
    status: 'IN_PROGRESS',
    createdAt: '2026-09-15T08:15:00Z',
    updatedAt: '2026-09-15T10:20:00Z',
    labName: 'National Type Evaluation Laboratory (Synthetic)',
    operatorName: 'Alex Morgan · Lead Metrologist',
    totalProcedures: 10,
    passedProcedures: 4,
    summary: 'Multi-range Class III instrument evaluation currently in progress. Partial weighing ranges derived.',
  },
]
