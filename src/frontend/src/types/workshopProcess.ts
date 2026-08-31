/**
 * Der lokale Entwurf eines Werkstattvorgangs.
 *
 * Weitere Angaben aus dem Backend oder der KI-Extraktion können später an
 * diesem Typ ergänzt werden, ohne den Startvorgang zu verändern.
 */
export type WorkshopProcess = {
  serviceType: WorkshopProcessType
  status: WorkshopProcessStatus
  /** Normalisiertes Kennzeichen, z. B. `CW-AB 123`. */
  licensePlate: string
  /**
   * Der lokale Entwurf folgt dem bestehenden RegistrationDraft-Vertrag:
   * Stammdaten des Satzes, Profiltiefen und Zustände bleiben getrennt.
   */
  tireSets: WorkshopTireSet[]
  tireInspections: WorkshopTireInspection[]
  conditions: WorkshopTireCondition[]
}

export type WorkshopProcessType = 'tire_change' | 'tire_storage'

export type WorkshopProcessStatus = 'draft'

export type TireSetRole = 'installed' | 'removed' | 'stored'

export type TireType = 'summer' | 'winter' | 'all_season' | 'unknown'

export type TireConditionType =
  | 'ok'
  | 'worn'
  | 'uneven_wear'
  | 'inner_wear'
  | 'outer_wear'
  | 'damaged'
  | 'cracked'
  | 'foreign_object'
  | 'low_tread'
  | 'unknown'

export type TireSetDraft = {
  tireType?: TireType
  widthMm?: number
  aspectRatio?: number
  rimDiameterInch?: number
  manufacturer?: string
  model?: string
  quantity?: number
  notes?: string
}

export type WorkshopTireSet = {
  role: TireSetRole
  tireSet: TireSetDraft
}

export type WorkshopTireInspection = {
  tireSetRole: TireSetRole
  treadFrontMm?: number
  treadRearMm?: number
}

export type WorkshopTireCondition = {
  tireSetRole: TireSetRole
  condition?: TireConditionType
  /** Die manuelle Basisansicht bewertet den gesamten Reifensatz. */
  position: 'all'
}
