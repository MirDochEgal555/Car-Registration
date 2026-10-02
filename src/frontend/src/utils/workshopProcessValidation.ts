import type { WorkshopProcess } from '../types/workshopProcess'
import type { FrontendErrorKind } from '../types/frontendError'

export type WorkshopProcessValidationIssue = {
  field: string
  kind: Extract<FrontendErrorKind, 'required' | 'invalid'>
  message: string
  section: 'plate' | 'tires' | 'service'
}

/**
 * Validiert die Werte, die die manuelle Erfassung aktuell verwaltet.
 *
 * Die Reifenangaben sind in der bestehenden Erfassung optional; sobald sie
 * eingegeben wurden, dürfen sie jedoch nicht unplausibel sein. Ein Kennzeichen
 * kann ebenfalls leer bleiben.
 */
export function getWorkshopProcessValidationIssues(
  process: WorkshopProcess,
): WorkshopProcessValidationIssue[] {
  const issues: WorkshopProcessValidationIssue[] = []
  const tireSetEntry = process.tireSets[0]
  if (!tireSetEntry) return issues

  const expectedTireSetRole = process.serviceType === 'tire_storage' ? 'stored' : 'installed'

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

  if (
    process.serviceType === 'tire_change' &&
    process.tireChangeDetails?.wheelChangePerformed === undefined
  ) {
    issues.push({
      field: 'Räderwechsel',
      kind: 'required',
      message: 'Bitte angeben, ob ein Räderwechsel durchgeführt wurde.',
      section: 'service',
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
