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
    installGetUserMedia(() =>
      Promise.reject(new DOMException('Permission denied', 'NotAllowedError')),
    )
    vi.stubGlobal('MediaRecorder', MediaRecorderMock)
    const user = userEvent.setup()

    render(<RecorderHarness />)
    await user.click(screen.getByRole('button', { name: 'Aufnahme starten' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /Mikrofonzugriff wurde nicht erlaubt/,
    )
    expect(screen.getByRole('button', { name: 'Aufnahme starten' })).toBeVisible()
  })
})
