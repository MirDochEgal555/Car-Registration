/**
 * Der lokale Entwurf eines Werkstattvorgangs.
 *
 * Weitere Angaben aus dem Backend oder der KI-Extraktion können später an
 * diesem Typ ergänzt werden, ohne den Startvorgang zu verändern.
 */
export type WorkshopProcess = {
  serviceType: WorkshopProcessType
  status: WorkshopProcessStatus
}

export type WorkshopProcessType = 'tire_change' | 'tire_storage'

export type WorkshopProcessStatus = 'draft'
