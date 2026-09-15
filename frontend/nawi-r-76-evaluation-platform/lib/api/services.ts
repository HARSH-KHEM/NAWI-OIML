/**
 * Typed API services connecting frontend components to FastAPI endpoints.
 * Authoritative standard: OIML R 76-1:2006 (E).
 * Fallback to realistic synthetic laboratory seed fixtures if backend is offline.
 */

import { apiClient, ApiError } from './client'
import {
  InstrumentRead,
  InstrumentCreate,
  InstrumentConfigurationRead,
  InstrumentConfigurationCreate,
  EvaluationRead,
  EvaluationCreate,
  EvaluationPlanResponse,
  EvaluationTestRead,
} from '@/lib/types/domain'
import { MOCK_INSTRUMENTS, MOCK_EVALUATIONS } from '@/lib/mock-data'

/**
 * Convert a MockInstrument into an InstrumentRead + active configuration
 */
function mockToInstrumentRead(mock: (typeof MOCK_INSTRUMENTS)[0]): InstrumentRead {
  const config: InstrumentConfigurationRead = {
    id: `cfg-${mock.id}`,
    instrument_id: mock.id,
    accuracy_class: mock.accuracyClass,
    max_capacity: mock.maxCapacity,
    min_capacity: mock.minCapacity,
    verification_scale_interval: mock.verificationScaleInterval,
    actual_scale_interval: mock.actualScaleInterval,
    unit: mock.unit,
    number_of_ranges: mock.numberOfRanges,
    is_multiple_range: mock.isMultipleRange,
    tare_type: mock.tareType,
    is_electronic: mock.isElectronic,
    has_zero_setting: mock.hasZeroSetting,
    extra_capabilities: {
      load_receptor: {
        support_count: mock.loadReceptor.supportCount,
        special_receptor: mock.loadReceptor.specialReceptor,
        rolling_load: mock.loadReceptor.rollingLoad,
      },
    },
    ranges: mock.isMultipleRange
      ? [
          {
            range_index: 1,
            min_capacity: '0.100',
            max_capacity: '15.000',
            verification_scale_interval: '0.005',
            actual_scale_interval: '0.005',
            unit: mock.unit,
          },
          {
            range_index: 2,
            min_capacity: '0.200',
            max_capacity: '30.000',
            verification_scale_interval: '0.010',
            actual_scale_interval: '0.010',
            unit: mock.unit,
          },
        ]
      : [],
    is_active: true,
    created_at: '2026-03-01T08:00:00Z',
  }

  return {
    id: mock.id,
    manufacturer: mock.manufacturer,
    model_name: mock.modelName,
    instrument_family: mock.instrumentFamily,
    serial_number: mock.serialNumber,
    status: mock.status,
    is_synthetic: mock.isSynthetic,
    created_at: '2026-03-01T08:00:00Z',
    configurations: [config],
  }
}

// In-memory runtime cache for client-created instruments when in demo/offline mode
const runtimeInstruments: InstrumentRead[] = []
const runtimeEvaluations: EvaluationRead[] = []

/**
 * Fetch all registered instruments.
 */
export async function getInstruments(): Promise<InstrumentRead[]> {
  try {
    const instruments = await apiClient<InstrumentRead[]>('/instruments')
    // Attempt to enrich each instrument with its configurations
    const enriched = await Promise.all(
      instruments.map(async (inst) => {
        try {
          const configs = await apiClient<InstrumentConfigurationRead[]>(
            `/instruments/${inst.id}/configurations`
          )
          return { ...inst, configurations: configs }
        } catch {
          return inst
        }
      })
    )
    return [...runtimeInstruments, ...enriched]
  } catch (err) {
    console.warn('API /instruments unreachable, using laboratory fixtures:', err)
    const mockList = MOCK_INSTRUMENTS.map(mockToInstrumentRead)
    return [...runtimeInstruments, ...mockList]
  }
}

/**
 * Fetch a single instrument by ID with its configurations.
 */
export async function getInstrument(id: string): Promise<InstrumentRead | null> {
  // Check runtime cache first
  const cached = runtimeInstruments.find((i) => i.id === id)
  if (cached) return cached

  try {
    const inst = await apiClient<InstrumentRead>(`/instruments/${id}`)
    try {
      const configs = await apiClient<InstrumentConfigurationRead[]>(
        `/instruments/${id}/configurations`
      )
      return { ...inst, configurations: configs }
    } catch {
      return inst
    }
  } catch {
    const mock = MOCK_INSTRUMENTS.find((i) => i.id === id)
    if (mock) return mockToInstrumentRead(mock)
    return null
  }
}

/**
 * Create a new weighing instrument identity.
 */
export async function createInstrument(payload: InstrumentCreate): Promise<InstrumentRead> {
  try {
    return await apiClient<InstrumentRead>('/instruments', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  } catch (err) {
    console.warn('API createInstrument fallback:', err)
    const simulated: InstrumentRead = {
      id: `inst-${Date.now().toString(36)}`,
      manufacturer: payload.manufacturer,
      model_name: payload.model_name,
      instrument_family: payload.instrument_family || 'NAWI',
      serial_number: payload.serial_number,
      status: payload.status || 'DRAFT',
      is_synthetic: payload.is_synthetic ?? false,
      created_at: new Date().toISOString(),
      configurations: [],
    }
    runtimeInstruments.unshift(simulated)
    return simulated
  }
}

/**
 * Create and attach a metrological configuration to an instrument.
 */
export async function createInstrumentConfiguration(
  instrumentId: string,
  payload: InstrumentConfigurationCreate
): Promise<InstrumentConfigurationRead> {
  try {
    return await apiClient<InstrumentConfigurationRead>(
      `/instruments/${instrumentId}/configurations`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    )
  } catch (err) {
    console.warn('API createConfiguration fallback:', err)
    const simulatedConfig: InstrumentConfigurationRead = {
      id: `cfg-${Date.now().toString(36)}`,
      instrument_id: instrumentId,
      accuracy_class: payload.accuracy_class,
      max_capacity: payload.max_capacity,
      min_capacity: payload.min_capacity,
      verification_scale_interval: payload.verification_scale_interval,
      actual_scale_interval: payload.actual_scale_interval,
      unit: payload.unit || 'kg',
      number_of_ranges: payload.number_of_ranges || 1,
      is_multiple_range: payload.is_multiple_range ?? false,
      tare_type: payload.tare_type || 'SUBTRACTIVE',
      is_electronic: payload.is_electronic ?? true,
      has_zero_setting: payload.has_zero_setting ?? true,
      extra_capabilities: payload.extra_capabilities || {},
      ranges: (payload.ranges || []).map((r) => ({
        range_index: r.range_index,
        min_capacity: r.min_capacity,
        max_capacity: r.max_capacity,
        verification_scale_interval: r.verification_scale_interval,
        actual_scale_interval: r.actual_scale_interval,
        unit: r.unit || payload.unit || 'kg',
      })),
      is_active: true,
      created_at: new Date().toISOString(),
    }

    // Attach to runtime cached instrument if exists
    const inst = runtimeInstruments.find((i) => i.id === instrumentId)
    if (inst) {
      if (!inst.configurations) inst.configurations = []
      inst.configurations.unshift(simulatedConfig)
    }

    return simulatedConfig
  }
}

/**
 * Fetch all evaluations.
 */
export async function getEvaluations(): Promise<EvaluationRead[]> {
  try {
    const list = await apiClient<EvaluationRead[]>('/evaluations')
    return [...runtimeEvaluations, ...list]
  } catch (err) {
    console.warn('API /evaluations unreachable, using mock data:', err)
    return [...runtimeEvaluations]
  }
}

/**
 * Fetch a single evaluation by ID.
 */
export async function getEvaluation(id: string): Promise<EvaluationRead | null> {
  const cached = runtimeEvaluations.find((e) => e.id === id || e.evaluation_number === id)
  if (cached) return cached

  try {
    return await apiClient<EvaluationRead>(`/evaluations/${id}`)
  } catch {
    return null
  }
}

/**
 * Initialize a new evaluation and capture immutable snapshot.
 */
export async function createEvaluation(
  instrumentId: string,
  payload: EvaluationCreate
): Promise<EvaluationRead> {
  try {
    return await apiClient<EvaluationRead>(`/instruments/${instrumentId}/evaluations`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  } catch (err) {
    console.warn('API createEvaluation fallback:', err)
    // Find instrument
    const inst = await getInstrument(instrumentId)
    const activeConfig = inst?.configurations?.[0]

    const evalNumber = payload.evaluation_number || `EV-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`
    const simulatedEval: EvaluationRead = {
      id: `eval-${Date.now().toString(36)}`,
      evaluation_number: evalNumber,
      instrument_id: instrumentId,
      instrument_configuration_id: activeConfig?.id || `cfg-${instrumentId}`,
      rule_version_id: payload.rule_version_id || '2006-01',
      configuration_snapshot: {
        accuracy_class: activeConfig?.accuracy_class || 'CLASS_III',
        max_capacity: String(activeConfig?.max_capacity || '30.000'),
        min_capacity: String(activeConfig?.min_capacity || '0.200'),
        verification_scale_interval: String(activeConfig?.verification_scale_interval || '0.010'),
        actual_scale_interval: String(activeConfig?.actual_scale_interval || '0.010'),
        unit: activeConfig?.unit || 'kg',
        number_of_ranges: activeConfig?.number_of_ranges || 1,
        is_multiple_range: activeConfig?.is_multiple_range ?? false,
        tare_type: activeConfig?.tare_type || 'SUBTRACTIVE',
        is_electronic: activeConfig?.is_electronic ?? true,
        has_zero_setting: activeConfig?.has_zero_setting ?? true,
        extra_capabilities: activeConfig?.extra_capabilities || {},
        ranges: activeConfig?.ranges?.map((r) => ({
          range_index: r.range_index,
          min_capacity: String(r.min_capacity),
          max_capacity: String(r.max_capacity),
          verification_scale_interval: String(r.verification_scale_interval),
          actual_scale_interval: String(r.actual_scale_interval),
          unit: r.unit,
        })),
        snapshot_timestamp: new Date().toISOString(),
        instrument_serial: inst?.serial_number || 'UNKNOWN-SN',
        manufacturer: inst?.manufacturer || 'Unknown',
        model_name: inst?.model_name || 'Unknown',
      },
      status: 'IN_PROGRESS',
      operator_id: payload.operator_id,
      lab_name: payload.lab_name || 'National Metrology Institute',
      created_at: new Date().toISOString(),
    }

    runtimeEvaluations.unshift(simulatedEval)
    return simulatedEval
  }
}

/**
 * Generate plan for an evaluation.
 */
export async function generateEvaluationPlan(evaluationId: string): Promise<EvaluationPlanResponse> {
  try {
    return await apiClient<EvaluationPlanResponse>(`/evaluations/${evaluationId}/generate-plan`, {
      method: 'POST',
    })
  } catch (err) {
    console.warn('API generatePlan fallback:', err)
    const evalRecord = await getEvaluation(evaluationId)
    const isMulti = evalRecord?.configuration_snapshot?.is_multiple_range ?? false

    return {
      evaluation_id: evaluationId,
      evaluation_number: evalRecord?.evaluation_number || evaluationId,
      status: 'IN_PROGRESS',
      configuration_snapshot: evalRecord?.configuration_snapshot as any,
      tests: [],
      total_tests: isMulti ? 10 : 9,
      applicable_tests_count: isMulti ? 6 : 4,
    }
  }
}

/**
 * Fetch generated test plan.
 */
export async function getEvaluationPlan(evaluationId: string): Promise<EvaluationPlanResponse | null> {
  try {
    return await apiClient<EvaluationPlanResponse>(`/evaluations/${evaluationId}/plan`)
  } catch {
    return null
  }
}

/**
 * Fetch tests for an evaluation.
 */
export async function getEvaluationTests(evaluationId: string): Promise<EvaluationTestRead[]> {
  try {
    return await apiClient<EvaluationTestRead[]>(`/evaluations/${evaluationId}/tests`)
  } catch {
    return []
  }
}
