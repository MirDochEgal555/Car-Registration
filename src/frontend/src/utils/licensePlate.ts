import type { FrontendErrorKind } from '../types/frontendError'

const LICENSE_PLATE_PATTERN = /^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s\d{1,4}[A-Z]?$/

export type LicensePlateValidationError = {
  kind: Extract<FrontendErrorKind, 'required' | 'invalid'>
  message: string
}

/**
 * Bringt explizit eingegebene deutsche Kennzeichen in eine einheitliche Form,
 * ohne fehlende Zeichen zu erraten.
 */
export function normalizeLicensePlate(value: string): string {
  const parts = value
    .trim()
    .toLocaleUpperCase('de-DE')
    .split(/[-\s]+/)
    .filter(Boolean)

  if (parts.length >= 3) {
    return `${parts[0]}-${parts[1]} ${parts.slice(2).join('')}`
  }

  if (parts.length === 2) {
    return `${parts[0]}-${parts[1]}`
  }

  return parts[0] ?? ''
}

export function getLicensePlateError(value: string): string | null {
  return getLicensePlateValidationError(value)?.message ?? null
}

export function getLicensePlateValidationError(
  value: string,
): LicensePlateValidationError | null {
  if (!value) {
    return {
      kind: 'required',
      message: 'Kennzeichen eingeben.',
    }
  }

  if (!LICENSE_PLATE_PATTERN.test(value)) {
    return {
      kind: 'invalid',
      message: 'Kennzeichen prüfen, z. B. CW-AB 123.',
    }
  }

  return null
}
