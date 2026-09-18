import type { ApiRegistrationDraft } from '../types/registrationApi'
import type {
  TireConditionType,
  TireType,
  WorkshopProcess,
} from '../types/workshopProcess'

const tireTypes = new Set<TireType>([
  'summer',
  'winter',
  'all_season',
  'unknown',
])

const tireConditions = new Set<TireConditionType>([
  'ok',
  'worn',
  'uneven_wear',
  'inner_wear',
  'outer_wear',
  'damaged',
  'cracked',
  'foreign_object',
  'low_tread',
  'unknown',
])

/**
 * Apply one backend-generated draft to the editable workshop model.
 * The browser-owned ID and original transcript stay stable for idempotent
 * delivery and review; every structured value comes from the explicit
 * extraction action.
 */
export function mapExtractionToWorkshopProcess(
  currentProcess: WorkshopProcess,
  draft: ApiRegistrationDraft,
): WorkshopProcess {
  const defaultRole = draft.service_type === 'tire_storage' ? 'stored' : 'installed'
  const tireSets = draft.tire_sets.map(({ role, tire_set }) => ({
    role,
    tireSet: {
      tireType: asTireType(tire_set.tire_type),
      widthMm: tire_set.width_mm,
      aspectRatio: tire_set.aspect_ratio,
      rimDiameterInch: tire_set.rim_diameter_inch,
      manufacturer: tire_set.manufacturer,
      model: tire_set.model,
      quantity: tire_set.quantity,
      notes: tire_set.notes,
    },
  }))
  const tireInspections = draft.tire_inspections.map((inspection) => ({
    tireSetRole: inspection.tire_set_role,
    treadFrontMm: inspection.tread_front_mm,
    treadRearMm: inspection.tread_rear_mm,
  }))
  const conditions = draft.conditions.map((condition) => ({
    tireSetRole: condition.tire_set_role,
    condition: asTireCondition(condition.condition),
    position: condition.position,
  }))

  return {
    id: currentProcess.id,
    status: 'draft',
    serviceType: draft.service_type,
    licensePlate: draft.vehicle.license_plate,
    rawTranscript: currentProcess.rawTranscript ?? draft.raw_transcript,
    // The UI always exposes one editable row. An empty extraction means
    // “nothing heard”, never “do not allow manual entry”.
    tireSets: tireSets.length > 0 ? tireSets : [{ role: defaultRole, tireSet: {} }],
    tireInspections:
      tireInspections.length > 0 ? tireInspections : [{ tireSetRole: defaultRole }],
    conditions:
      conditions.length > 0
        ? conditions
        : [{ tireSetRole: defaultRole, position: 'all' }],
    ...(draft.service_type === 'tire_change'
      ? {
          tireChangeDetails: {
            wheelChangePerformed:
              draft.tire_change_details?.wheel_change_performed,
          },
        }
      : {}),
  }
}

function asTireType(value: string | undefined): TireType | undefined {
  return value && tireTypes.has(value as TireType)
    ? (value as TireType)
    : undefined
}

function asTireCondition(
  value: string | undefined,
): TireConditionType | undefined {
  return value && tireConditions.has(value as TireConditionType)
    ? (value as TireConditionType)
    : undefined
}
