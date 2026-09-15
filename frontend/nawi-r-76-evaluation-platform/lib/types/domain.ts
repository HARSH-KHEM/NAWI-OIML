/**
 * Strict TypeScript mirrors of backend Pydantic schemas and SQLAlchemy models.
 * Authoritative Standard: OIML R 76-1:2006 (E)
 */

export type AccuracyClass = 'CLASS_I' | 'CLASS_II' | 'CLASS_III' | 'CLASS_IIII'
export type TareType = 'SUBTRACTIVE' | 'ADDITIVE' | 'NONE'
export type InstrumentStatus = 'ACTIVE' | 'DRAFT' | 'RETIRED'
export type EvaluationStatus = 'DRAFT' | 'IN_PROGRESS' | 'COMPLIANT' | 'NON_COMPLIANT' | 'CANCELLED'
export type EvaluationTestStatus = 'NOT_APPLICABLE' | 'APPLICABLE' | 'IN_PROGRESS' | 'COMPLETED' | 'INCOMPLETE'
export type TestAttemptStatus = 'IN_PROGRESS' | 'COMPLETED' | 'SUPERSEDED'
export type ComplianceDecision = 'PASS' | 'FAIL' | 'INCOMPLETE' | 'N_A'
export type ImplementationStatus = 'IMPLEMENTED' | 'PARTIAL' | 'APPLICABILITY_ONLY'
export type ScopeType = 'INSTRUMENT' | 'RANGE'

export interface LoadReceptorGeometry {
  support_count?: number
  special_receptor?: boolean
  rolling_load?: boolean
  reverse_direction?: boolean
}

export interface InstrumentConfigurationRange {
  id?: string
  range_index: number
  min_capacity: string | number
  max_capacity: string | number
  verification_scale_interval: string | number
  actual_scale_interval: string | number
  unit: string
}

export interface InstrumentConfigurationRead {
  id: string
  instrument_id: string
  accuracy_class: AccuracyClass
  max_capacity: string | number
  min_capacity: string | number
  verification_scale_interval: string | number
  actual_scale_interval: string | number
  unit: string
  number_of_ranges: number
  is_multiple_range: boolean
  tare_type: TareType
  is_electronic: boolean
  has_zero_setting: boolean
  extra_capabilities?: {
    synthetic_fixture?: boolean
    type?: string
    load_receptor?: LoadReceptorGeometry
    [key: string]: any
  }
  ranges: InstrumentConfigurationRange[]
  is_active: boolean
  created_at: string
}

export interface InstrumentRead {
  id: string
  manufacturer: string
  model_name: string
  instrument_family: string
  serial_number: string
  status: InstrumentStatus
  is_synthetic: boolean
  created_at: string
  updated_at?: string
  configurations?: InstrumentConfigurationRead[]
}

export interface ConfigurationSnapshot {
  accuracy_class: AccuracyClass
  max_capacity: string
  min_capacity: string
  verification_scale_interval: string
  actual_scale_interval: string
  unit: string
  number_of_ranges: number
  is_multiple_range: boolean
  tare_type: TareType
  is_electronic: boolean
  has_zero_setting: boolean
  extra_capabilities?: {
    load_receptor?: LoadReceptorGeometry
    [key: string]: any
  }
  ranges?: Array<{
    range_index: number
    min_capacity: string
    max_capacity: string
    verification_scale_interval: string
    actual_scale_interval: string
    unit: string
  }>
  snapshot_timestamp: string
  instrument_serial: string
  manufacturer: string
  model_name: string
}

export interface EvaluationRead {
  id: string
  evaluation_number: string
  instrument_id: string
  instrument_configuration_id: string
  rule_version_id: string
  configuration_snapshot: ConfigurationSnapshot
  status: EvaluationStatus
  operator_id?: string
  lab_name?: string
  created_at: string
  completed_at?: string
}

export interface EvaluationTestRead {
  id: string
  evaluation_id: string
  test_definition_id: string
  rule_version_id?: string
  sequence: number
  status: EvaluationTestStatus
  scope_type: ScopeType
  range_reference?: string
  range_index?: number
  applicability_reason?: string
  implementation_status: ImplementationStatus
  test_code: string
  title: string
  r76_reference: string
  attempts?: TestAttemptRead[]
}

export interface TestAttemptRead {
  id: string
  evaluation_test_id: string
  attempt_number: number
  status: TestAttemptStatus
  started_at: string
  completed_at?: string
  supersedes_attempt_id?: string
  notes?: string
  steps?: Array<{
    id: string
    step_code: string
    step_name: string
    sequence: number
    description?: string
  }>
  observations?: ObservationRead[]
}

export interface ObservationRead {
  id: string
  test_attempt_id: string
  test_step_id?: string
  observation_code: string
  value_numeric?: string | number
  value_text?: string
  value_json?: Record<string, any>
  unit?: string
  entered_by?: string
  recorded_at: string
  notes?: string
}

export interface CalculationRead {
  id: string
  test_attempt_id: string
  calculation_name: string
  formula_reference: string
  inputs_json: Record<string, any>
  outputs_json: Record<string, any>
  calculated_at: string
}

export interface ComplianceResultRead {
  id: string
  test_attempt_id: string
  calculation_id?: string
  decision: ComplianceDecision
  criterion_value?: string
  measured_value?: string
  margin?: string | number
  rule_version_id?: string
  reasoning_json?: Record<string, any>
  decided_at: string
}

export interface TraceRecord {
  compliance: {
    decision: ComplianceDecision
    criterion_value?: string
    margin?: string | number
    reasoning?: Record<string, any>
  }
  calculation?: {
    name: string
    formula: string
    inputs: Record<string, any>
    outputs: Record<string, any>
  }
  raw_observations: Array<{
    code: string
    value: string | number
    unit?: string
    recorded_at: string
  }>
  test_attempt: {
    attempt_number: number
    status: TestAttemptStatus
  }
  evaluation_test: {
    test_code: string
    title: string
    r76_reference: string
  }
  configuration_snapshot: ConfigurationSnapshot
  rule_version?: {
    standard_version: string
    version_number: string
    content_hash?: string
  }
  instrument: {
    manufacturer: string
    model_name: string
    serial_number: string
  }
}
