import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ExtractionApiError,
  extractRegistrationFromTranscript,
} from './extractionApi'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => vi.unstubAllGlobals())

describe('extractRegistrationFromTranscript', () => {
  it('sends the verbatim transcript to the extraction route', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        registration: { id: 'id' },
        valid: true,
        review_required: false,
        issues: [],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await extractRegistrationFromTranscript('  M-AB 6350, Sommerreifen.  ')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/extractions',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ transcript: '  M-AB 6350, Sommerreifen.  ' }),
      }),
    )
  })

  it('keeps backend extraction errors actionable for the UI', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: 'Die KI-Extraktion ist zurzeit nicht verfügbar.' }, 503),
      ),
    )

    await expect(extractRegistrationFromTranscript('Notiz')).rejects.toEqual(
      expect.objectContaining<Partial<ExtractionApiError>>({
        name: 'ExtractionApiError',
        status: 503,
        message: 'Die KI-Extraktion ist zurzeit nicht verfügbar.',
      }),
    )
  })
})
