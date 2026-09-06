const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const AUDIO_TRANSCRIPTION_URL = `${API_BASE_URL}/api/v1/audio/transcribe`

type AudioTranscriptionErrorResponse = {
  status?: unknown
  transcript?: unknown
  error?: {
    code?: unknown
    message?: unknown
  }
}

type AudioTranscriptionSuccessResponse = {
  status: 'completed'
  transcript: string
}

export class AudioTranscriptionApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(message)
    this.name = 'AudioTranscriptionApiError'
  }
}

/** Upload a browser recording and return its plain-text transcript. */
export async function transcribeAudioRecording(audio: Blob): Promise<string> {
  const formData = new FormData()
  formData.append('audio', audio, 'workshop-notiz.webm')

  let response: Response
  try {
    response = await fetch(AUDIO_TRANSCRIPTION_URL, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: formData,
    })
  } catch {
    throw new AudioTranscriptionApiError(
      'Die Sprachnotiz konnte nicht hochgeladen werden. Bitte Verbindung prüfen und erneut versuchen.',
      0,
      null,
    )
  }

  const body = await readResponseBody(response)
  if (!response.ok) {
    throw new AudioTranscriptionApiError(
      getErrorMessage(body, response.status),
      response.status,
      body,
    )
  }

  if (!isCompletedTranscription(body)) {
    throw new AudioTranscriptionApiError(
      'Die Sprachtranskription hat keinen lesbaren Text zurückgegeben. Bitte erneut versuchen.',
      response.status,
      body,
    )
  }

  // The transcript is an audit value. Validate that it contains speech, but
  // do not alter the provider's text before it is attached to the session.
  return body.transcript
}

export function canRetryAudioTranscription(error: unknown): boolean {
  if (!(error instanceof AudioTranscriptionApiError)) {
    return true
  }

  // A malformed success response has no usable transcript either; retrying the
  // same recording is safe and may recover from a transient provider response.
  return (
    error.status === 0 ||
    error.status === 429 ||
    error.status >= 500 ||
    (error.status >= 200 && error.status < 300)
  )
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    return response.text()
  }

  try {
    return await response.json()
  } catch {
    return null
  }
}

function isCompletedTranscription(
  body: unknown,
): body is AudioTranscriptionSuccessResponse {
  return (
    typeof body === 'object' &&
    body !== null &&
    'status' in body &&
    body.status === 'completed' &&
    'transcript' in body &&
    typeof body.transcript === 'string' &&
    body.transcript.trim().length > 0
  )
}

function getErrorMessage(body: unknown, status: number): string {
  if (isAudioTranscriptionErrorResponse(body)) {
    const message = body.error?.message
    if (typeof message === 'string' && message.trim()) {
      return message
    }
  }

  return `Die Sprachtranskription konnte nicht verarbeitet werden (HTTP ${status}).`
}

function isAudioTranscriptionErrorResponse(
  body: unknown,
): body is AudioTranscriptionErrorResponse {
  return typeof body === 'object' && body !== null
}
