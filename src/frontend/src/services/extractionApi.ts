import type { ApiValidationResponse } from '../types/registrationApi'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const EXTRACTION_URL = `${API_BASE_URL}/api/v1/extractions`

export class ExtractionApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(message)
    this.name = 'ExtractionApiError'
  }
}

/** Create a reviewable registration draft from an unchanged transcript. */
export async function extractRegistrationFromTranscript(
  transcript: string,
): Promise<ApiValidationResponse> {
  let response: Response
  try {
    response = await fetch(EXTRACTION_URL, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript }),
    })
  } catch {
    throw new ExtractionApiError(
      'Der KI-Vorschlag konnte nicht erstellt werden. Bitte Verbindung prüfen und erneut versuchen.',
      0,
      null,
    )
  }

  const body = await readResponseBody(response)
  if (!response.ok || !isValidationResponse(body)) {
    throw new ExtractionApiError(
      getErrorMessage(body, response.status),
      response.status,
      body,
    )
  }

  return body
}

async function readResponseBody(response: Response): Promise<unknown> {
  if ((response.headers.get('content-type') || '').includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return null
    }
  }
  return response.text()
}

function isValidationResponse(value: unknown): value is ApiValidationResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'registration' in value &&
    'issues' in value &&
    Array.isArray(value.issues)
  )
}

function getErrorMessage(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
  }
  return `Der KI-Vorschlag konnte nicht erstellt werden (HTTP ${status}).`
}
