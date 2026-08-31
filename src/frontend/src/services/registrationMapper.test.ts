import { describe, expect, it } from 'vitest'
import type { WorkshopProcess } from '../types/workshopProcess'
import { mapWorkshopProcessToRegistration } from './registrationMapper'

describe('mapWorkshopProcessToRegistration', () => {
  it('übersetzt Formularfelder verlustfrei in den FastAPI-Vertrag', () => {
    const process: WorkshopProcess = {
      id: '0d5a1322-0574-4cef-a024-f89b567e4321',
      serviceType: 'tire_change',
      status: 'draft',
      licensePlate: 'CW-AB 123',
      tireSets: [
        {
          role: 'installed',
          tireSet: {
            tireType: 'winter',
            widthMm: 205,
            aspectRatio: 55,
            rimDiameterInch: 16,
            manufacturer: 'Continental',
            model: 'WinterContact TS 870',
            quantity: 4,
            notes: 'Satz prüfen',
          },
        },
      ],
      tireInspections: [
        { tireSetRole: 'installed', treadFrontMm: 6.5, treadRearMm: 6 },
      ],
      conditions: [
        { tireSetRole: 'installed', condition: 'ok', position: 'all' },
      ],
      tireChangeDetails: { wheelChangePerformed: true },
    }

    expect(mapWorkshopProcessToRegistration(process, true)).toMatchObject({
      id: process.id,
      service_type: 'tire_change',
      mechanic_confirmed: true,
      vehicle: { license_plate: 'CW-AB 123' },
      tire_sets: [
        {
          role: 'installed',
          tire_set: {
            tire_type: 'winter',
            width_mm: 205,
            aspect_ratio: 55,
            rim_diameter_inch: 16,
            manufacturer: 'Continental',
            model: 'WinterContact TS 870',
            quantity: 4,
            notes: 'Satz prüfen',
          },
        },
      ],
      tire_inspections: [
        {
          tire_set_role: 'installed',
          tread_front_mm: 6.5,
          tread_rear_mm: 6,
        },
      ],
      conditions: [
        { tire_set_role: 'installed', condition: 'ok', position: 'all' },
      ],
      tire_change_details: { wheel_change_performed: true },
    })
  })
})
