import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  AudioTranscriptionApiError,
  canRetryAudioTranscription,
  transcribeAudioRecording,
} from './audioApi'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('transcribeAudioRecording', () => {
  it('uploads the completed browser recording as multipart data and returns the transcript', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        status: 'completed',
        transcript: '  Sommerreifen vorne links geprüft.  ',
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      transcribeAudioRecording(new Blob(['audio'], { type: 'audio/webm' })),
    ).resolves.toBe('  Sommerreifen vorne links geprüft.  ')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/audio/transcribe',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      }),
    )
    const request = fetchMock.mock.calls[0]?.[1] as RequestInit
    const uploadedAudio = (request.body as FormData).get('audio')
    expect(uploadedAudio).toBeInstanceOf(Blob)
    expect((uploadedAudio as File).name).toBe('workshop-notiz.webm')
  })

  it('preserves a retryable API failure for the UI', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            status: 'failed',
            transcript: null,
            error: {
              code: 'transcription_failed',
              message: 'Die Sprachtranskription ist fehlgeschlagen.',
            },
          },
          502,
        ),
      ),
    )

    await expect(
      transcribeAudioRecording(new Blob(['audio'], { type: 'audio/webm' })),
    ).rejects.toMatchObject({
      name: 'AudioTranscriptionApiError',
      status: 502,
      message: 'Die Sprachtranskription ist fehlgeschlagen.',
    })

    expect(
      canRetryAudioTranscription(
        new AudioTranscriptionApiError('Fehlgeschlagen', 502, null),
      ),
    ).toBe(true)
    expect(
      canRetryAudioTranscription(
        new AudioTranscriptionApiError('Ungültiges Audio', 422, null),
      ),
    ).toBe(false)
  })
})
