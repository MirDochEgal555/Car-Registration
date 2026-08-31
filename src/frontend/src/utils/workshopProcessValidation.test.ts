import { describe, expect, it } from 'vitest'
import type { WorkshopProcess } from '../types/workshopProcess'
import { getWorkshopProcessValidationIssues } from './workshopProcessValidation'

function createProcess(): WorkshopProcess {
  return {
    serviceType: 'tire_storage',
    status: 'draft',
    licensePlate: 'CW-AB 123',
    tireSets: [
      {
        role: 'stored',
        tireSet: {
          widthMm: 205,
          aspectRatio: 55,
          rimDiameterInch: 17,
          quantity: 4,
        },
      },
    ],
    tireInspections: [
      {
        tireSetRole: 'stored',
        treadFrontMm: 6.5,
        treadRearMm: 6,
      },
    ],
    conditions: [{ tireSetRole: 'stored', position: 'all' }],
  }
}

describe('Vorgangsvalidierung', () => {
  it('akzeptiert einen vollständigen Einlagerungsentwurf', () => {
    expect(getWorkshopProcessValidationIssues(createProcess())).toEqual([])
  })

  it('meldet unplausible Reifenwerte und eine falsche Satzrolle', () => {
    const process = createProcess()
    process.tireSets[0] = {
      role: 'installed',
      tireSet: { widthMm: 100, quantity: 0 },
    }

    expect(getWorkshopProcessValidationIssues(process)).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: 'Reifensatz' }),
        expect.objectContaining({ field: 'Reifenbreite' }),
        expect.objectContaining({ field: 'Reifenmenge' }),
      ]),
    )
  })
})
