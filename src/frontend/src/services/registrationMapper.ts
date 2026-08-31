import type { WorkshopProcess } from '../types/workshopProcess'
import type { ApiRegistrationDraft } from '../types/registrationApi'

/** Temporary MVP identity until the frontend receives an authenticated user. */
const DEFAULT_MECHANIC_ID = '3c0a5fe3-b1b7-4f9f-a9e0-4fc653c2a96e'

function getMechanicId(): string {
  return import.meta.env.VITE_MECHANIC_ID || DEFAULT_MECHANIC_ID
}

function today(): string {
  // A workshop protocol belongs to the mechanic's local calendar day, not the
  // UTC day around midnight.
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/** Translate the camelCase interaction model into FastAPI's snake_case DTO. */
export function mapWorkshopProcessToRegistration(
  process: WorkshopProcess,
  mechanicConfirmed = false,
): ApiRegistrationDraft {
  return {
    id: process.id,
    service_type: process.serviceType,
    service_date: today(),
    mechanic_id: getMechanicId(),
    mechanic_confirmed: mechanicConfirmed,
    vehicle: {
      license_plate: process.licensePlate,
    },
    tire_sets: process.tireSets.map(({ role, tireSet }) => ({
      role,
      tire_set: {
        tire_type: tireSet.tireType,
        width_mm: tireSet.widthMm,
        aspect_ratio: tireSet.aspectRatio,
        rim_diameter_inch: tireSet.rimDiameterInch,
        manufacturer: tireSet.manufacturer,
        model: tireSet.model,
        quantity: tireSet.quantity,
        notes: tireSet.notes,
      },
    })),
    tire_inspections: process.tireInspections.map((inspection) => ({
      tire_set_role: inspection.tireSetRole,
      tread_front_mm: inspection.treadFrontMm,
      tread_rear_mm: inspection.treadRearMm,
    })),
    conditions: process.conditions.map((condition) => ({
      tire_set_role: condition.tireSetRole,
      condition: condition.condition,
      position: condition.position,
    })),
    ...(process.serviceType === 'tire_change'
      ? {
          tire_change_details: {
            wheel_change_performed:
              process.tireChangeDetails?.wheelChangePerformed,
          },
        }
      : {}),
  }
}
