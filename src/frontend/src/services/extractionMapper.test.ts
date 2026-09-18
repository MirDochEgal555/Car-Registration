import { describe, expect, it } from 'vitest'
import type { ApiRegistrationDraft } from '../types/registrationApi'
import type { WorkshopProcess } from '../types/workshopProcess'
import { mapExtractionToWorkshopProcess } from './extractionMapper'

describe('mapExtractionToWorkshopProcess', () => {
  it('uses extracted values while preserving the browser ID and original transcript', () => {
    const current: WorkshopProcess = {
      id: 'browser-owned-id',
      status: 'draft',
      serviceType: 'tire_storage',
      licensePlate: 'ALT-1',
      rawTranscript: 'M-AB 6350 mit Winterreifen.',
      tireSets: [],
      tireInspections: [],
      conditions: [],
    }
    const draft: ApiRegistrationDraft = {
      id: 'backend-id',
      service_type: 'tire_change',
      service_date: '2026-09-17',
      mechanic_id: 'mechanic-id',
      mechanic_confirmed: false,
      vehicle: { license_plate: 'M-AB 6350' },
      tire_sets: [
        {
          role: 'installed',
          tire_set: { tire_type: 'winter', width_mm: 205, quantity: 4 },
        },
      ],
      tire_inspections: [{ tire_set_role: 'installed', tread_front_mm: 6.5 }],
      conditions: [{ tire_set_role: 'installed', condition: 'ok', position: 'all' }],
      tire_change_details: { wheel_change_performed: true },
    }

    expect(mapExtractionToWorkshopProcess(current, draft)).toMatchObject({
      id: 'browser-owned-id',
      rawTranscript: 'M-AB 6350 mit Winterreifen.',
      serviceType: 'tire_change',
      licensePlate: 'M-AB 6350',
      tireSets: [
        { role: 'installed', tireSet: { tireType: 'winter', widthMm: 205, quantity: 4 } },
      ],
      tireChangeDetails: { wheelChangePerformed: true },
    })
  })

  it('keeps empty extraction results manually editable', () => {
    const current: WorkshopProcess = {
      id: 'browser-owned-id',
      status: 'draft',
      serviceType: 'tire_change',
      licensePlate: '',
      tireSets: [],
      tireInspections: [],
      conditions: [],
    }
    const draft: ApiRegistrationDraft = {
      id: 'backend-id',
      service_type: 'tire_storage',
      service_date: '2026-09-17',
      mechanic_id: 'mechanic-id',
      mechanic_confirmed: false,
      vehicle: { license_plate: '' },
      tire_sets: [],
      tire_inspections: [],
      conditions: [],
    }

    expect(mapExtractionToWorkshopProcess(current, draft)).toMatchObject({
      tireSets: [{ role: 'stored', tireSet: {} }],
      tireInspections: [{ tireSetRole: 'stored' }],
      conditions: [{ tireSetRole: 'stored', position: 'all' }],
    })
  })
})
