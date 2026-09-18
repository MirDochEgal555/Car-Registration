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
 * Merge one backend-generated draft into the editable workshop model.
 *
 * A mechanic can continue typing while transcription and extraction run.  An
 * extraction is therefore a suggestion: it fills blank browser fields but
 * never silently replaces a value already entered by a person.  The selected
 * service type is browser-owned for the same reason; a spoken phrase must not
 * change the process that the mechanic explicitly started.
 */
export function mapExtractionToWorkshopProcess(
  currentProcess: WorkshopProcess,
  draft: ApiRegistrationDraft,
): WorkshopProcess {
  const defaultRole = getDefaultRole(currentProcess.serviceType)
  const extractedTireSets = (draft.tire_sets ?? []).map(({ role, tire_set }) => ({
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
  const extractedTireInspections = (draft.tire_inspections ?? []).map((inspection) => ({
    tireSetRole: inspection.tire_set_role,
    treadFrontMm: inspection.tread_front_mm,
    treadRearMm: inspection.tread_rear_mm,
  }))
  const extractedConditions = (draft.conditions ?? []).map((condition) => ({
    tireSetRole: condition.tire_set_role,
    condition: asTireCondition(condition.condition),
    position: condition.position,
  }))

  return {
    id: currentProcess.id,
    status: 'draft',
    serviceType: currentProcess.serviceType,
    licensePlate: currentProcess.licensePlate || draft.vehicle.license_plate,
    rawTranscript: currentProcess.rawTranscript ?? draft.raw_transcript,
    // The UI always exposes one editable row. An empty extraction means
    // “nothing heard”, never “do not allow manual entry”.
    tireSets: mergeTireSets(
      currentProcess.tireSets,
      extractedTireSets,
      defaultRole,
    ),
    tireInspections:
      mergeTireInspections(
        currentProcess.tireInspections,
        extractedTireInspections,
        defaultRole,
      ),
    conditions:
      mergeConditions(currentProcess.conditions, extractedConditions, defaultRole),
    ...(currentProcess.serviceType === 'tire_change'
      ? {
          tireChangeDetails: {
            wheelChangePerformed: chooseManualValue(
              currentProcess.tireChangeDetails?.wheelChangePerformed,
              draft.tire_change_details?.wheel_change_performed,
            ),
          },
        }
      : {}),
  }
}

function getDefaultRole(serviceType: WorkshopProcess['serviceType']) {
  return serviceType === 'tire_storage' ? 'stored' : 'installed'
}

function mergeTireSets(
  current: WorkshopProcess['tireSets'],
  extracted: WorkshopProcess['tireSets'],
  defaultRole: WorkshopProcess['tireSets'][number]['role'],
): WorkshopProcess['tireSets'] {
  const currentFirst = current[0]
  const extractedFirst = extracted[0]
  const first = {
    role: currentFirst?.role ?? defaultRole,
    tireSet: {
      tireType: chooseManualValue(currentFirst?.tireSet.tireType, extractedFirst?.tireSet.tireType),
      widthMm: chooseManualValue(currentFirst?.tireSet.widthMm, extractedFirst?.tireSet.widthMm),
      aspectRatio: chooseManualValue(currentFirst?.tireSet.aspectRatio, extractedFirst?.tireSet.aspectRatio),
      rimDiameterInch: chooseManualValue(currentFirst?.tireSet.rimDiameterInch, extractedFirst?.tireSet.rimDiameterInch),
      manufacturer: chooseManualValue(currentFirst?.tireSet.manufacturer, extractedFirst?.tireSet.manufacturer),
      model: chooseManualValue(currentFirst?.tireSet.model, extractedFirst?.tireSet.model),
      quantity: chooseManualValue(currentFirst?.tireSet.quantity, extractedFirst?.tireSet.quantity),
      notes: chooseManualValue(currentFirst?.tireSet.notes, extractedFirst?.tireSet.notes),
    },
  }

  return [first, ...extracted.slice(1)]
}

function mergeTireInspections(
  current: WorkshopProcess['tireInspections'],
  extracted: WorkshopProcess['tireInspections'],
  defaultRole: WorkshopProcess['tireInspections'][number]['tireSetRole'],
): WorkshopProcess['tireInspections'] {
  const currentFirst = current[0]
  const extractedFirst = extracted[0]
  return [
    {
      tireSetRole: currentFirst?.tireSetRole ?? defaultRole,
      treadFrontMm: chooseManualValue(currentFirst?.treadFrontMm, extractedFirst?.treadFrontMm),
      treadRearMm: chooseManualValue(currentFirst?.treadRearMm, extractedFirst?.treadRearMm),
    },
    ...extracted.slice(1),
  ]
}

function mergeConditions(
  current: WorkshopProcess['conditions'],
  extracted: WorkshopProcess['conditions'],
  defaultRole: WorkshopProcess['conditions'][number]['tireSetRole'],
): WorkshopProcess['conditions'] {
  const currentFirst = current[0]
  const extractedFirst = extracted[0]
  return [
    {
      tireSetRole: currentFirst?.tireSetRole ?? defaultRole,
      condition: chooseManualValue(currentFirst?.condition, extractedFirst?.condition),
      position: 'all',
    },
    ...extracted.slice(1),
  ]
}

function chooseManualValue<T>(manualValue: T | undefined, extractedValue: T | undefined) {
  return manualValue ?? extractedValue
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
