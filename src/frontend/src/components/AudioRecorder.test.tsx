import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AudioRecorder } from './AudioRecorder'

type RecorderHarnessProps = {
  onAudioRecorded?: (audio: Blob) => void
  onAudioRemoved?: () => void
}

function RecorderHarness({
  onAudioRecorded = () => undefined,
  onAudioRemoved = () => undefined,
}: RecorderHarnessProps) {
  const [audio, setAudio] = useState<Blob | null>(null)

  return (
    <AudioRecorder
      audioBlob={audio}
      onAudioRecorded={(recording) => {
        setAudio(recording)
        onAudioRecorded(recording)
      }}
      onAudioRemoved={() => {
        setAudio(null)
        onAudioRemoved()
      }}
      onRetryTranscription={() => undefined}
      transcriptionState={{ kind: 'idle' }}
    />
  )
}

class MediaRecorderMock {
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

class FailingMediaRecorderMock extends MediaRecorderMock {
  start() {
    super.start()
    this.onerror?.(new Event('error'))
  }
}

class UnsupportedWebmMediaRecorderMock extends MediaRecorderMock {
  static isTypeSupported() {
    return false
  }
}

function installGetUserMedia(getUserMedia: () => Promise<MediaStream>) {
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
  Reflect.deleteProperty(navigator, 'mediaDevices')
})

describe('AudioRecorder', () => {
  it('speichert eine beendete Browseraufnahme temporär als Blob', async () => {
    const stopTrack = vi.fn()
    const stream = {
      getTracks: () => [{ stop: stopTrack }],
    } as unknown as MediaStream
    const getUserMedia = vi.fn().mockResolvedValue(stream)
    const onAudioRecorded = vi.fn()
    const onAudioRemoved = vi.fn()
    installGetUserMedia(getUserMedia)
    vi.stubGlobal('MediaRecorder', MediaRecorderMock)
    const user = userEvent.setup()

    render(
      <RecorderHarness
        onAudioRecorded={onAudioRecorded}
        onAudioRemoved={onAudioRemoved}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))
    expect(await screen.findByText(/Aufnahme läuft/)).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Aufnahme stoppen' }))

    expect(await screen.findByText(/Aufnahme gespeichert/)).toBeVisible()
    expect(onAudioRecorded).toHaveBeenCalledOnce()
    expect(onAudioRecorded.mock.calls[0]?.[0]).toBeInstanceOf(Blob)
    expect(onAudioRecorded.mock.calls[0]?.[0].size).toBeGreaterThan(0)
    expect(stopTrack).toHaveBeenCalledOnce()

    await user.click(screen.getByRole('button', { name: 'Aufnahme verwerfen' }))

    expect(onAudioRemoved).toHaveBeenCalledOnce()
    expect(screen.getByRole('button', { name: 'Aufnahme starten' })).toBeVisible()
  })

  it('zeigt eine verständliche Meldung, wenn der Mikrofonzugriff abgelehnt wird', async () => {
    const getUserMedia = vi.fn().mockRejectedValue(
      new DOMException('Permission denied', 'NotAllowedError'),
    )
    installGetUserMedia(getUserMedia)
    vi.stubGlobal('MediaRecorder', MediaRecorderMock)
    const user = userEvent.setup()

    render(<RecorderHarness />)
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /Mikrofonzugriff wurde nicht erlaubt/,
    )
    expect(
      screen.getByRole('heading', { name: 'Mikrofonzugriff nicht erlaubt' }),
    ).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Aufnahme erneut versuchen' }),
    ).toBeVisible()
    await user.click(
      screen.getByRole('button', { name: 'Aufnahme erneut versuchen' }),
    )
    expect(getUserMedia).toHaveBeenCalledTimes(2)
  })

  it('erklärt eine nicht verfügbare MediaRecorder-API und lässt den Versuch wiederholen', async () => {
    installGetUserMedia(vi.fn())
    const user = userEvent.setup()

    render(<RecorderHarness />)
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))

    expect(
      await screen.findByRole('heading', { name: 'Audioaufnahme nicht verfügbar' }),
    ).toBeVisible()
    expect(screen.getByText(/unterstützt keine audioaufnahme/i)).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Aufnahme erneut versuchen' }),
    ).toBeVisible()
  })

  it('lehnt einen Browser ohne unterstützte WebM-Aufnahme ab, ohne die manuelle Erfassung zu blockieren', async () => {
    const stopTrack = vi.fn()
    const stream = {
      getTracks: () => [{ stop: stopTrack }],
    } as unknown as MediaStream
    installGetUserMedia(vi.fn().mockResolvedValue(stream))
    vi.stubGlobal('MediaRecorder', UnsupportedWebmMediaRecorderMock)
    const user = userEvent.setup()

    render(<RecorderHarness />)
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))

    expect(
      await screen.findByRole('heading', { name: 'Audioaufnahme nicht verfügbar' }),
    ).toBeVisible()
    expect(screen.getByText(/keine unterstützte webm-audioaufnahme/i)).toBeVisible()
    expect(screen.getByText(/manuell erfassen/i)).toBeVisible()
    expect(stopTrack).toHaveBeenCalledOnce()
  })

  it('meldet einen Aufnahmeabbruch und erhält die Retry-Aktion', async () => {
    const stream = {
      getTracks: () => [{ stop: vi.fn() }],
    } as unknown as MediaStream
    const getUserMedia = vi.fn().mockResolvedValue(stream)
    installGetUserMedia(getUserMedia)
    vi.stubGlobal('MediaRecorder', FailingMediaRecorderMock)
    const user = userEvent.setup()

    render(<RecorderHarness />)
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))

    expect(
      await screen.findByRole('heading', { name: 'Aufnahme fehlgeschlagen' }),
    ).toBeVisible()
    expect(screen.getByText(/audioaufnahme wurde unterbrochen/i)).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Aufnahme erneut versuchen' }),
    ).toBeVisible()
    await user.click(
      screen.getByRole('button', { name: 'Aufnahme erneut versuchen' }),
    )
    expect(getUserMedia).toHaveBeenCalledTimes(2)
  })
})
