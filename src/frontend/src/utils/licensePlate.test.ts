import { describe, expect, it } from 'vitest'
import {
  getLicensePlateValidationError,
  normalizeLicensePlate,
} from './licensePlate'

describe('Kennzeichen-Verarbeitung', () => {
  it('behält die Freitext-Eingabe unverändert bei', () => {
    const licensePlate = normalizeLicensePlate(' cw  ab   123 ')

    expect(licensePlate).toBe(' cw  ab   123 ')
    expect(getLicensePlateValidationError(licensePlate)).toBeNull()
  })

  it('akzeptiert auch ein leeres Kennzeichen', () => {
    expect(getLicensePlateValidationError('')).toBeNull()
    expect(getLicensePlateValidationError('NOT-A PLATE')).toBeNull()
  })
})
