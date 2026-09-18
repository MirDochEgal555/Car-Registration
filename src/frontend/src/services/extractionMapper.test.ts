import { describe, expect, it } from 'vitest'
import type { ApiRegistrationDraft } from '../types/registrationApi'
import type { WorkshopProcess } from '../types/workshopProcess'
import { mapExtractionToWorkshopProcess } from './extractionMapper'

describe('mapExtractionToWorkshopProcess', () => {
  it('fills blank values from extraction while preserving browser-owned workflow choices', () => {
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
      serviceType: 'tire_storage',
      licensePlate: 'ALT-1',
      tireSets: [
        { role: 'stored', tireSet: { tireType: 'winter', widthMm: 205, quantity: 4 } },
      ],
    })
  })

  it('never replaces mechanic-entered values while an extraction is running', () => {
    const current: WorkshopProcess = {
      id: 'browser-owned-id',
      status: 'draft',
      serviceType: 'tire_change',
      licensePlate: 'CW-AB 123',
      tireSets: [
        {
          role: 'installed',
          tireSet: { manufacturer: 'Continental', quantity: 4 },
        },
      ],
      tireInspections: [{ tireSetRole: 'installed', treadFrontMm: 6 }],
      conditions: [{ tireSetRole: 'installed', condition: 'ok', position: 'all' }],
      tireChangeDetails: { wheelChangePerformed: false },
    }
    const draft: ApiRegistrationDraft = {
      id: 'backend-id',
      service_type: 'tire_storage',
      service_date: '2026-09-17',
      mechanic_id: 'mechanic-id',
      mechanic_confirmed: false,
      vehicle: { license_plate: 'M-XY 42' },
      tire_sets: [
        {
          role: 'stored',
          tire_set: {
            tire_type: 'winter',
            manufacturer: 'Michelin',
            model: 'Alpin 6',
            quantity: 2,
          },
        },
      ],
      tire_inspections: [{ tire_set_role: 'stored', tread_front_mm: 5 }],
      conditions: [{ tire_set_role: 'stored', condition: 'worn', position: 'all' }],
      tire_change_details: { wheel_change_performed: true },
    }

    expect(mapExtractionToWorkshopProcess(current, draft)).toMatchObject({
      serviceType: 'tire_change',
      licensePlate: 'CW-AB 123',
      tireSets: [
        {
          role: 'installed',
          tireSet: {
            tireType: 'winter',
            manufacturer: 'Continental',
            model: 'Alpin 6',
            quantity: 4,
          },
        },
      ],
      tireInspections: [{ tireSetRole: 'installed', treadFrontMm: 6 }],
      conditions: [{ tireSetRole: 'installed', condition: 'ok', position: 'all' }],
      tireChangeDetails: { wheelChangePerformed: false },
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
      tireSets: [{ role: 'installed', tireSet: {} }],
      tireInspections: [{ tireSetRole: 'installed' }],
      conditions: [{ tireSetRole: 'installed', position: 'all' }],
    })
  })
})
