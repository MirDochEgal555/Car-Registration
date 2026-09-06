import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

function startNewProcess() {
  return userEvent.setup()
}

function getSummarySection(label: string) {
  const section = screen.getByText(label, { selector: 'p' }).closest('section')

  if (!section) {
    throw new Error(`Zusammenfassung für ${label} nicht gefunden.`)
  }

  return section
}

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function deferred<T>() {
  let resolve: (value: T | PromiseLike<T>) => void = () => undefined
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })

  return { promise, resolve }
}

function validRegistration(licensePlate: string) {
  return {
    valid: true,
    review_required: false,
    issues: [],
    registration: { vehicle: { license_plate: licensePlate } },
  }
}

function emailSent() {
  return {
    registration_id: 'c2feb07e-4854-4ef8-9e8a-14d8468df624',
    status: 'email_sent',
    recipient: 'office@example.com',
    attempt_count: 1,
    submitted_at: '2026-08-31T10:00:00Z',
  }
}

class AudioMediaRecorderMock {
  state: RecordingState = 'inactive'
  mimeType = 'audio/webm'
  ondataavailable: ((event: BlobEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onstop: ((event: Event) => void) | null = null

  start() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'inactive'
    this.ondataavailable?.({
      data: new Blob(['Werkstattnotiz'], { type: this.mimeType }),
    } as BlobEvent)
    this.onstop?.(new Event('stop'))
  }
}

function installAudioRecording() {
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: vi.fn() }],
      } as unknown as MediaStream),
    },
  })
  vi.stubGlobal('MediaRecorder', AudioMediaRecorderMock)
}

describe('Mechaniker → FastAPI → E-Mail-Workflow', () => {
  beforeEach(() => {
    window.location.hash = ''
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    Reflect.deleteProperty(navigator, 'mediaDevices')
  })

  it('lädt die Aufnahme hoch, zeigt den Text und behält manuell erfasste Daten bei', async () => {
    const transcriptionRequest = deferred<Response>()
    const fetchMock = vi.fn().mockReturnValue(transcriptionRequest.promise)
    vi.stubGlobal('fetch', fetchMock)
    installAudioRecording()
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Reifenwechsel' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    fireEvent.change(screen.getByLabelText(/Hersteller/), {
      target: { value: 'Continental' },
    })

    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))
    await user.click(screen.getByRole('button', { name: 'Aufnahme stoppen' }))

    expect(
      await screen.findByRole('heading', { name: 'Sprachnotiz wird verarbeitet' }),
    ).toBeVisible()
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/v1/audio/transcribe')
    const request = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(request.body).toBeInstanceOf(FormData)

    transcriptionRequest.resolve(
      response({
        status: 'completed',
        transcript: 'Vorne links bitte Profiltiefe prüfen.',
      }),
    )

    expect(
      await screen.findByRole('heading', { name: 'Gesprochene Notiz' }),
    ).toBeVisible()
    expect(screen.getByText('Vorne links bitte Profiltiefe prüfen.')).toBeVisible()
    expect(screen.getByLabelText(/Kennzeichen/)).toHaveValue('CW-AB 123')
    expect(screen.getByLabelText(/Hersteller/)).toHaveValue('Continental')
  })

  it('speichert das unveränderte Transkript mit dem Vorgang, ohne Formularwerte daraus abzuleiten', async () => {
    const transcript = '  Abweichendes Kennzeichen: CW ZZ 999.  \n'
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ status: 'completed', transcript }))
      .mockResolvedValueOnce(response(validRegistration('CW-AB 123')))
      .mockResolvedValueOnce(response(emailSent()))
    vi.stubGlobal('fetch', fetchMock)
    installAudioRecording()
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))
    await user.click(screen.getByRole('button', { name: 'Aufnahme stoppen' }))
    expect(
      await screen.findByRole('heading', { name: 'Gesprochene Notiz' }),
    ).toBeVisible()

    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('heading', { name: 'Alles erledigt.' }),
    ).toBeVisible()
    const validationPayload = JSON.parse(
      String((fetchMock.mock.calls[1]?.[1] as RequestInit).body),
    )
    const sendPayload = JSON.parse(
      String((fetchMock.mock.calls[2]?.[1] as RequestInit).body),
    )
    expect(validationPayload).toMatchObject({
      raw_transcript: transcript,
      vehicle: { license_plate: 'CW-AB 123' },
    })
    expect(sendPayload).toMatchObject({
      raw_transcript: transcript,
      vehicle: { license_plate: 'CW-AB 123' },
    })
  })

  it('bietet nach einer fehlgeschlagenen Transkription einen Retry mit derselben Aufnahme an', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        response(
          {
            status: 'failed',
            transcript: null,
            error: {
              code: 'transcription_provider_unavailable',
              message: 'Der Sprachtranskriptionsdienst ist zurzeit nicht verfügbar.',
            },
          },
          503,
        ),
      )
      .mockResolvedValueOnce(
        response({
          status: 'completed',
          transcript: 'Räder nachziehen.',
        }),
      )
    vi.stubGlobal('fetch', fetchMock)
    installAudioRecording()
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))
    await user.click(screen.getByRole('button', { name: 'Aufnahme stoppen' }))

    expect(
      await screen.findByRole('button', {
        name: 'Transkription erneut versuchen',
      }),
    ).toBeVisible()
    await user.click(
      screen.getByRole('button', { name: 'Transkription erneut versuchen' }),
    )

    expect(await screen.findByText('Räder nachziehen.')).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('mappt einen Reifenwechsel, prüft ihn und übergibt ihn an die Büro-E-Mail', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 123')))
      .mockResolvedValueOnce(response(emailSent()))
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Reifenwechsel' }))

    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    fireEvent.change(screen.getByLabelText(/Hersteller/), {
      target: { value: 'Continental' },
    })
    await user.click(screen.getByLabelText('Ja'))
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    expect(fetchMock).not.toHaveBeenCalled()
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('heading', { name: 'Alles erledigt.' }),
    ).toBeVisible()
    expect(screen.getByText('E-Mail erfolgreich versendet')).toBeVisible()
    expect(screen.getByText(/e-mail wurde an office@example.com übergeben/i)).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0]?.[0]).toContain('/api/v1/registrations/validate')
    expect(fetchMock.mock.calls[1]?.[0]).toContain('/api/v1/registrations/send')

    const sendPayload = JSON.parse(
      String((fetchMock.mock.calls[1]?.[1] as RequestInit).body),
    )
    expect(sendPayload).toMatchObject({
      service_type: 'tire_change',
      mechanic_confirmed: true,
      vehicle: { license_plate: 'CW-AB 123' },
      tire_sets: [{ role: 'installed', tire_set: { manufacturer: 'Continental' } }],
      tire_change_details: { wheel_change_performed: true },
    })
  })

  it('zeigt den Versandstatus, während die bestätigte E-Mail übergeben wird', async () => {
    const emailRequest = deferred<Response>()
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 123')))
      .mockReturnValueOnce(emailRequest.promise)
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Reifenwechsel' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    fireEvent.change(screen.getByLabelText(/Hersteller/), {
      target: { value: 'Continental' },
    })
    await user.click(screen.getByLabelText('Ja'))
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('heading', { name: 'E-Mail wird versendet' }),
    ).toBeVisible()
    expect(
      screen.getByRole('button', { name: /e-mail wird versendet/i }),
    ).toBeDisabled()

    emailRequest.resolve(response(emailSent()))

    expect(
      await screen.findByRole('heading', { name: 'Alles erledigt.' }),
    ).toBeVisible()
    expect(screen.getByText('E-Mail erfolgreich versendet')).toBeVisible()
  })

  it('zeigt Backend-Validierung an, ohne einen ungültigen Vorgang zu versenden', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      response({
        valid: false,
        review_required: true,
        registration: { vehicle: { license_plate: 'CW-AB 123' } },
        issues: [
          {
            field: 'tire_sets.0.tire_set.width_mm',
            code: 'implausible_value',
            message: 'Die Reifenbreite ist unplausibel.',
            status: 'invalid',
          },
        ],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(await screen.findByRole('heading', { name: 'Backend-Validierung' })).toBeVisible()
    expect(screen.getByText('Reifenbreite:')).toBeVisible()
    expect(screen.getByText('Die Reifenbreite ist unplausibel.')).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('behält Fahrzeug- und Reifendaten nach einem Versandfehler und bietet einen Retry an', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 987')))
      .mockResolvedValueOnce(
        response(
          {
            detail: {
              message: 'Der Versand ist fehlgeschlagen. Der Vorgang wurde gespeichert und kann erneut versendet werden.',
              delivery: {
                registration_id: 'c2feb07e-4854-4ef8-9e8a-14d8468df624',
                status: 'email_failed',
                attempt_count: 1,
                last_error: 'The office email could not be delivered.',
              },
            },
          },
          502,
        ),
      )
      .mockResolvedValueOnce(response({ ...emailSent(), attempt_count: 2 }))
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 987' },
    })
    fireEvent.change(screen.getByLabelText(/Hersteller/), {
      target: { value: 'Goodyear' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('button', { name: 'Erneut senden' }),
    ).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Versand fehlgeschlagen' }),
    ).toBeVisible()
    expect(
      screen.getByText(/alle erfassten fahrzeug- und reifendaten bleiben erhalten/i),
    ).toBeVisible()
    expect(screen.getByText('CW-AB 987')).toBeVisible()
    expect(screen.getByText('Goodyear')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Erneut senden' })).toHaveClass(
      'primary-action',
    )
    await user.click(screen.getByRole('button', { name: 'Erneut senden' }))

    expect(
      await screen.findByText(/versand nach 2 versuchen erfolgreich/i),
    ).toBeVisible()
    expect(fetchMock.mock.calls[2]?.[0]).toMatch(/\/registrations\/[\w-]+\/retry$/)
  })

  it('startet bei schnellen Mehrfachklicks nur einen Versand', async () => {
    const emailRequest = deferred<Response>()
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 123')))
      .mockReturnValueOnce(emailRequest.promise)
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Reifenwechsel' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    await user.click(screen.getByLabelText('Ja'))
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    const sendButton = screen.getByRole('button', {
      name: /vorgang bestätigen.*senden/i,
    })
    fireEvent.click(sendButton)
    fireEvent.click(sendButton)

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(
      await screen.findByRole('heading', { name: 'E-Mail wird versendet' }),
    ).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    emailRequest.resolve(response(emailSent()))

    expect(
      await screen.findByRole('heading', { name: 'Alles erledigt.' }),
    ).toBeVisible()
  })

  it('blockiert eine fehlerhafte Einlagerung bis zur Korrektur', async () => {
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))

    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'not a plate' },
    })
    fireEvent.change(screen.getByLabelText('Breite'), {
      target: { value: '100' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    expect(
      screen.getByRole('heading', { name: 'Vorgang kann nicht bestätigt werden' }),
    ).toBeVisible()
    expect(screen.getByText('Reifenbreite:')).toBeVisible()
    expect(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    ).toBeDisabled()

    const plateSection = getSummarySection('Kennzeichen')
    await user.click(
      within(plateSection).getByRole('button', { name: 'Bearbeiten' }),
    )
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 987' },
    })
    await user.click(screen.getByRole('button', { name: 'Fertig' }))

    const tireSection = getSummarySection('Reifendaten')
    await user.click(
      within(tireSection).getByRole('button', { name: 'Bearbeiten' }),
    )
    fireEvent.change(screen.getByLabelText('Breite (mm)'), {
      target: { value: '205' },
    })
    await user.click(screen.getByRole('button', { name: 'Fertig' }))

    expect(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    ).toBeEnabled()
  })
})
