import type {
  TireSetRole,
  WorkshopProcess,
} from '../types/workshopProcess'
import type { FrontendErrorKind } from '../types/frontendError'
import { getLicensePlateValidationError } from './licensePlate'

export type WorkshopProcessValidationIssue = {
  field: string
  kind: Extract<FrontendErrorKind, 'required' | 'invalid'>
  message: string
  section: 'plate' | 'tires'
}

/**
 * Validiert die Werte, die die manuelle Erfassung aktuell verwaltet.
 *
 * Das Kennzeichen ist für beide Vorgangstypen Pflicht. Die übrigen
 * Reifenangaben sind in der bestehenden Erfassung optional; sobald sie
 * eingegeben wurden, dürfen sie jedoch nicht unplausibel sein.
 */
export function getWorkshopProcessValidationIssues(
  process: WorkshopProcess,
): WorkshopProcessValidationIssue[] {
  const issues: WorkshopProcessValidationIssue[] = []
  const licensePlateError = getLicensePlateValidationError(process.licensePlate)

  if (licensePlateError) {
    issues.push({
      field: 'Kennzeichen',
      kind: licensePlateError.kind,
      message: licensePlateError.message,
      section: 'plate',
    })
  }

  const expectedTireSetRole: TireSetRole =
    process.serviceType === 'tire_storage' ? 'stored' : 'installed'
  const tireSetEntry = process.tireSets[0]

  if (!tireSetEntry) {
    issues.push({
      field: 'Reifensatz',
      kind: 'invalid',
      message: 'Zum gewählten Vorgang fehlt ein Reifensatz.',
      section: 'tires',
    })
    return issues
  }

  if (tireSetEntry.role !== expectedTireSetRole) {
    issues.push({
      field: 'Reifensatz',
      kind: 'invalid',
      message: 'Der Reifensatz passt nicht zum gewählten Vorgang.',
      section: 'tires',
    })
  }

  const tireSet = tireSetEntry.tireSet
  const tireInspection = process.tireInspections[0]
  const tireCondition = process.conditions[0]

  addRangeIssue(issues, 'Reifenbreite', tireSet.widthMm, 125, 405, 'mm')
  addRangeIssue(
    issues,
    'Reifenquerschnitt',
    tireSet.aspectRatio,
    20,
    95,
    '',
  )
  addRangeIssue(
    issues,
    'Felgendurchmesser',
    tireSet.rimDiameterInch,
    10,
    24,
    'Zoll',
  )
  addRangeIssue(issues, 'Reifenmenge', tireSet.quantity, 1, undefined, '')
  addRangeIssue(
    issues,
    'Profiltiefe vorne',
    tireInspection?.treadFrontMm,
    0,
    20,
    'mm',
  )
  addRangeIssue(
    issues,
    'Profiltiefe hinten',
    tireInspection?.treadRearMm,
    0,
    20,
    'mm',
  )

  if (tireInspection?.tireSetRole !== expectedTireSetRole) {
    issues.push({
      field: 'Profiltiefe',
      kind: 'invalid',
      message: 'Die Profiltiefe ist keinem passenden Reifensatz zugeordnet.',
      section: 'tires',
    })
  }

  if (tireCondition?.tireSetRole !== expectedTireSetRole) {
    issues.push({
      field: 'Zustand',
      kind: 'invalid',
      message: 'Der Zustand ist keinem passenden Reifensatz zugeordnet.',
      section: 'tires',
    })
  }

  return issues
}

function addRangeIssue(
  issues: WorkshopProcessValidationIssue[],
  field: string,
  value: number | undefined,
  minimum: number,
  maximum: number | undefined,
  unit: string,
) {
  if (
    value === undefined ||
    (value >= minimum && (maximum === undefined || value <= maximum))
  ) {
    return
  }

  const range = maximum === undefined ? `mindestens ${minimum}` : `${minimum}–${maximum}`
  issues.push({
    field,
    kind: 'invalid',
    message: `Wert muss ${range}${unit ? ` ${unit}` : ''} sein.`,
    section: 'tires',
  })
}
