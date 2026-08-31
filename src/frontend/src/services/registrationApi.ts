import type {
  ApiDeliveryStatus,
  ApiRegistrationDraft,
  ApiSendResponse,
  ApiValidationResponse,
} from '../types/registrationApi'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const API_PREFIX = `${API_BASE_URL}/api/v1/registrations`

export class RegistrationApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(message)
    this.name = 'RegistrationApiError'
  }
}

export async function validateRegistration(
  draft: ApiRegistrationDraft,
): Promise<ApiValidationResponse> {
  return request<ApiValidationResponse>('/validate', {
    method: 'POST',
    body: JSON.stringify(draft),
  })
}

export async function sendRegistration(
  draft: ApiRegistrationDraft,
): Promise<ApiSendResponse> {
  return request<ApiSendResponse>('/send', {
    method: 'POST',
    body: JSON.stringify(draft),
  })
}

export async function retryRegistrationDelivery(
  registrationId: string,
): Promise<ApiSendResponse> {
  return request<ApiSendResponse>(`/${encodeURIComponent(registrationId)}/retry`, {
    method: 'POST',
  })
}

export async function getRegistrationDeliveryStatus(
  registrationId: string,
): Promise<ApiDeliveryStatus> {
  return request<ApiDeliveryStatus>(
    `/${encodeURIComponent(registrationId)}/delivery-status`,
  )
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_PREFIX}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    })
  } catch {
    throw new RegistrationApiError(
      'Das Backend ist nicht erreichbar. Bitte Verbindung prüfen und erneut versuchen.',
      0,
      null,
    )
  }

  const body = await readResponseBody(response)
  if (!response.ok) {
    throw new RegistrationApiError(
      getErrorMessage(body, response.status),
      response.status,
      body,
    )
  }

  return body as T
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

function getErrorMessage(body: unknown, status: number): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const detail = body.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (
      typeof detail === 'object' &&
      detail !== null &&
      'message' in detail &&
      typeof detail.message === 'string'
    ) {
      return detail.message
    }
  }

  return `Die Anfrage konnte nicht verarbeitet werden (HTTP ${status}).`
}
