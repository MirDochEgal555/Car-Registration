import type { FrontendErrorKind } from '../types/frontendError'

export type LicensePlateValidationError = {
  kind: Extract<FrontendErrorKind, 'required' | 'invalid'>
  message: string
}

/**
 * Kennzeichen werden als Freitext behandelt und unverändert gespeichert.
 */
export function normalizeLicensePlate(value: string): string {
  return value
}

export function getLicensePlateError(value: string): string | null {
  return getLicensePlateValidationError(value)?.message ?? null
}

export function getLicensePlateValidationError(
  value: string,
): LicensePlateValidationError | null {
  if (!value.trim()) {
    return {
      kind: 'required',
      message: 'Kennzeichen eingeben.',
    }
  }

  return null
}
