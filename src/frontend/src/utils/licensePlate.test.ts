import { describe, expect, it } from 'vitest'
import {
  getLicensePlateValidationError,
  normalizeLicensePlate,
} from './licensePlate'

describe('Kennzeichen-Verarbeitung', () => {
  it('vereinheitlicht eine Eingabe und akzeptiert ein gültiges Kennzeichen', () => {
    const licensePlate = normalizeLicensePlate(' cw  ab   123 ')

    expect(licensePlate).toBe('CW-AB 123')
    expect(getLicensePlateValidationError(licensePlate)).toBeNull()
  })

  it('unterscheidet fehlende und ungültige Kennzeichen', () => {
    expect(getLicensePlateValidationError('')).toMatchObject({
      kind: 'required',
      message: 'Kennzeichen eingeben.',
    })
    expect(getLicensePlateValidationError('NOT-A PLATE')).toMatchObject({
      kind: 'invalid',
      message: 'Kennzeichen prüfen, z. B. CW-AB 123.',
    })
  })
})
