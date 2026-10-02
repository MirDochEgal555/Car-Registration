import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

class AudioMediaRecorderMock {
  state: RecordingState = 'inactive'
  mimeType = 'audio/webm'
  ondataavailable: ((event: BlobEvent) => void) | null = null
  onstop: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null

  start() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'inactive'
    this.ondataavailable?.({
      data: new Blob(['Werkstattnotiz'], { type: this.mimeType }),
    } as BlobEvent)
    this.onstop?.()
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

function response(body: unknown) {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('Aufnahme-Workflow', () => {
  beforeEach(() => {
    window.location.hash = ''
    window.sessionStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    Reflect.deleteProperty(navigator, 'mediaDevices')
    window.sessionStorage.clear()
  })

  it('startet ohne Vorgangsauswahl direkt in der Aufnahme', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Notiz aufnehmen' })).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Reifenwechsel' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Einlagerung' })).not.toBeInTheDocument()
    expect(screen.getAllByRole('textbox')).toHaveLength(1)
    expect(screen.getByLabelText(/Kennzeichen/)).toBeVisible()
  })

  it('speichert Transkript und Kennzeichen für die Prüfung', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(response({ status: 'completed', transcript: 'Räder bitte prüfen.' })),
    )
    installAudioRecording()
    const user = userEvent.setup()
    render(<App />)

    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))
    await user.click(screen.getByRole('button', { name: 'Aufnahme stoppen' }))

    expect(await screen.findByText('Räder bitte prüfen.')).toBeVisible()
    fireEvent.change(screen.getByLabelText('Transkript bearbeiten'), {
      target: { value: 'Räder wurden geprüft.' },
    })
    await user.click(screen.getByRole('button', { name: 'Aufnahme prüfen' }))

    expect(screen.getByRole('heading', { name: 'Transkript' })).toBeVisible()
    expect(screen.getByText('Räder wurden geprüft.')).toBeVisible()
    expect(screen.getByRole('textbox', { name: 'Kennzeichen' })).toHaveValue('cw ab 123')
    expect(screen.getByRole('button', { name: /aufnahme senden/i })).toBeEnabled()
  })
})
