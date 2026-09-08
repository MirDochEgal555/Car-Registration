import { useEffect, useRef, useState } from 'react'
import { FrontendErrorState } from './FrontendErrorState'

type RecorderState =
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'stopping'
  | 'recorded'
  | 'error'

export type AudioTranscriptionState =
  | { kind: 'idle' }
  | { kind: 'processing' }
  | { kind: 'completed'; transcript: string }
  | {
      kind: 'error'
      failureKind: 'upload' | 'transcription'
      message: string
      retryable: boolean
    }

type RecorderError = {
  kind: 'permission-denied' | 'media-recorder-unavailable' | 'recording-failed'
  message: string
}

type AudioRecorderProps = {
  audioBlob: Blob | null
  onAudioRecorded: (audio: Blob) => void
  onAudioRemoved: () => void
  onRecordingStarted?: () => void
  onRetryTranscription: () => void
  transcriptionState: AudioTranscriptionState
}

function stopMediaStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

function getMicrophoneError(error: unknown): RecorderError {
  if (!(error instanceof DOMException)) {
    return {
      kind: 'recording-failed',
      message: 'Die Audioaufnahme konnte nicht gestartet werden. Bitte erneut versuchen.',
    }
  }

  switch (error.name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return {
        kind: 'permission-denied',
        message:
          'Mikrofonzugriff wurde nicht erlaubt. Bitte erlaube das Mikrofon in den Browser-Einstellungen und versuche es erneut.',
      }
    case 'NotFoundError':
      return {
        kind: 'recording-failed',
        message:
          'Es wurde kein Mikrofon gefunden. Bitte ein Mikrofon verbinden und erneut versuchen.',
      }
    case 'NotReadableError':
    case 'AbortError':
      return {
        kind: 'recording-failed',
        message:
          'Das Mikrofon wird gerade von einer anderen App verwendet. Bitte diese schließen und erneut versuchen.',
      }
    default:
      return {
        kind: 'recording-failed',
        message: 'Die Audioaufnahme konnte nicht gestartet werden. Bitte erneut versuchen.',
      }
  }
}

function getRecorderErrorTitle(error: RecorderError): string {
  switch (error.kind) {
    case 'permission-denied':
      return 'Mikrofonzugriff nicht erlaubt'
    case 'media-recorder-unavailable':
      return 'Audioaufnahme nicht verfügbar'
    case 'recording-failed':
      return 'Aufnahme fehlgeschlagen'
  }
}

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60

  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function AudioRecorder({
  audioBlob,
  onAudioRecorded,
  onAudioRemoved,
  onRecordingStarted,
  onRetryTranscription,
  transcriptionState,
}: AudioRecorderProps) {
  const [recorderState, setRecorderState] = useState<RecorderState>(
    audioBlob ? 'recorded' : 'idle',
  )
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [recorderError, setRecorderError] = useState<RecorderError | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const recordingStartedAtRef = useRef<number | null>(null)
  const isMountedRef = useRef(false)
  const recordingFailedRef = useRef(false)
  const onAudioRecordedRef = useRef(onAudioRecorded)

  onAudioRecordedRef.current = onAudioRecorded

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
      const recorder = mediaRecorderRef.current
      if (recorder) {
        recorder.ondataavailable = null
        recorder.onstop = null
        recorder.onerror = null

        if (recorder.state !== 'inactive') {
          recorder.stop()
        }
      }

      stopMediaStream(mediaStreamRef.current)
      mediaRecorderRef.current = null
      mediaStreamRef.current = null
    }
  }, [])

  useEffect(() => {
    if (recorderState !== 'recording') {
      return
    }

    const intervalId = window.setInterval(() => {
      if (recordingStartedAtRef.current !== null) {
        setElapsedSeconds(
          Math.floor((Date.now() - recordingStartedAtRef.current) / 1000),
        )
      }
    }, 1_000)

    return () => window.clearInterval(intervalId)
  }, [recorderState])

  const releaseMicrophone = () => {
    stopMediaStream(mediaStreamRef.current)
    mediaStreamRef.current = null
    mediaRecorderRef.current = null
  }

  const startRecording = async () => {
    if (recorderState === 'requesting' || recorderState === 'recording') {
      return
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setRecorderState('error')
      setRecorderError({
        kind: 'recording-failed',
        message:
          'Dieser Browser unterstützt keinen Mikrofonzugriff. Bitte einen aktuellen Browser verwenden.',
      })
      return
    }

    if (!window.MediaRecorder) {
      setRecorderState('error')
      setRecorderError({
        kind: 'media-recorder-unavailable',
        message:
          'Dieser Browser unterstützt keine Audioaufnahme. Bitte einen aktuellen Browser verwenden.',
      })
      return
    }

    setRecorderState('requesting')
    setRecorderError(null)
    recordingFailedRef.current = false

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (error) {
      if (isMountedRef.current) {
        setRecorderState('error')
        setRecorderError(getMicrophoneError(error))
      }
      return
    }

    if (!isMountedRef.current) {
      stopMediaStream(stream)
      return
    }

    try {
      const recorder = new MediaRecorder(stream)
      const audioChunks: BlobPart[] = []

      mediaStreamRef.current = stream
      mediaRecorderRef.current = recorder
      recordingStartedAtRef.current = Date.now()
      setElapsedSeconds(0)

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      recorder.onerror = () => {
        recordingFailedRef.current = true
        if (isMountedRef.current) {
          setRecorderState('error')
          setRecorderError({
            kind: 'recording-failed',
            message: 'Die Audioaufnahme wurde unterbrochen. Bitte erneut versuchen.',
          })
        }
        releaseMicrophone()
      }

      recorder.onstop = () => {
        const duration = recordingStartedAtRef.current
          ? Math.max(
              1,
              Math.floor((Date.now() - recordingStartedAtRef.current) / 1000),
            )
          : 0
        recordingStartedAtRef.current = null

        if (!recordingFailedRef.current) {
          const audio = new Blob(audioChunks, {
            type: recorder.mimeType || 'audio/webm',
          })

          if (audio.size > 0) {
            onAudioRecordedRef.current(audio)
            if (isMountedRef.current) {
              setElapsedSeconds(duration)
              setRecorderState('recorded')
            }
          } else if (isMountedRef.current) {
            setRecorderState('error')
            setRecorderError({
              kind: 'recording-failed',
              message:
                'Es konnte keine Audiodatei gespeichert werden. Bitte erneut versuchen.',
            })
          }
        }

        releaseMicrophone()
      }

      recorder.start()
      onRecordingStarted?.()
      if (!recordingFailedRef.current) {
        setRecorderState('recording')
      }
    } catch {
      stopMediaStream(stream)
      mediaStreamRef.current = null
      mediaRecorderRef.current = null
      if (isMountedRef.current) {
        setRecorderState('error')
        setRecorderError({
          kind: 'recording-failed',
          message: 'Die Audioaufnahme konnte nicht gestartet werden. Bitte erneut versuchen.',
        })
      }
    }
  }

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') {
      return
    }

    setRecorderState('stopping')
    recorder.stop()
  }

  const removeRecording = () => {
    onAudioRemoved()
    setElapsedSeconds(0)
    setRecorderError(null)
    setRecorderState('idle')
  }

  const isRecording = recorderState === 'recording'
  const isStopping = recorderState === 'stopping'

  return (
    <section
      aria-labelledby="audio-recording-title"
      className={`audio-recorder${isRecording ? ' audio-recorder--recording' : ''}`}
    >
      <div className="audio-recorder__heading">
        <div>
          <p className="audio-recorder__eyebrow">Optional</p>
          <h2 id="audio-recording-title">Sprachnotiz</h2>
        </div>
        {isRecording && <span className="audio-recorder__live-indicator">Läuft</span>}
      </div>

      <p className="audio-recorder__description">
        Sprich Besonderheiten direkt am Fahrzeug ein. Nach dem Stoppen wird die
        Aufnahme sicher zur Transkription hochgeladen.
      </p>

      {isRecording && (
        <p aria-live="polite" className="audio-recorder__status" role="status">
          <span className="audio-recorder__recording-dot" aria-hidden="true" />
          Aufnahme läuft · {formatDuration(elapsedSeconds)}
        </p>
      )}

      {recorderState === 'requesting' && (
        <p aria-live="polite" className="audio-recorder__status" role="status">
          Mikrofon wird geöffnet …
        </p>
      )}

      {isStopping && (
        <p aria-live="polite" className="audio-recorder__status" role="status">
          Aufnahme wird gespeichert …
        </p>
      )}

      {recorderState === 'recorded' && audioBlob && (
        <p aria-live="polite" className="audio-recorder__status" role="status">
          ✓ Aufnahme gespeichert · {formatDuration(elapsedSeconds)}
        </p>
      )}

      {audioBlob && transcriptionState.kind === 'processing' && (
        <section
          aria-live="polite"
          className="audio-transcription audio-transcription--processing"
          role="status"
        >
          <span aria-hidden="true" className="audio-transcription__spinner" />
          <div>
            <h3>Sprachnotiz wird verarbeitet</h3>
            <p>Aufnahme wird hochgeladen und transkribiert …</p>
          </div>
        </section>
      )}

      {transcriptionState.kind === 'completed' && (
        <section
          aria-labelledby="audio-transcript-title"
          className="audio-transcription audio-transcription--completed"
        >
          <p className="audio-transcription__eyebrow">Transkript</p>
          <h3 id="audio-transcript-title">Gesprochene Notiz</h3>
          <p className="audio-transcription__text">
            {transcriptionState.transcript}
          </p>
          <p className="audio-transcription__hint">
            Das Transkript bleibt im Vorgang und ändert keine manuell erfassten
            Fahrzeug- oder Reifendaten.
          </p>
        </section>
      )}

      {audioBlob && transcriptionState.kind === 'error' && (
        <FrontendErrorState
          compact
          kind="unexpected"
          message={transcriptionState.message}
          title={
            transcriptionState.failureKind === 'upload'
              ? 'Audio-Upload fehlgeschlagen'
              : 'Transkription fehlgeschlagen'
          }
        >
          {transcriptionState.retryable && (
            <button
              className="audio-recorder__retry"
              onClick={onRetryTranscription}
              type="button"
            >
              Transkription erneut versuchen
            </button>
          )}
          <button
            className="audio-recorder__remove"
            onClick={removeRecording}
            type="button"
          >
            Neue Aufnahme erstellen
          </button>
        </FrontendErrorState>
      )}

      {recorderState === 'error' && recorderError && (
        <FrontendErrorState
          compact
          kind="unexpected"
          message={recorderError.message}
          title={getRecorderErrorTitle(recorderError)}
        />
      )}

      {isRecording || isStopping ? (
        <button
          aria-label={isStopping ? 'Speichert Aufnahme' : 'Aufnahme stoppen'}
          className="audio-recorder__stop"
          disabled={isStopping}
          onClick={stopRecording}
          type="button"
        >
          <span className="audio-recorder__stop-icon" aria-hidden="true" />
          {isStopping ? 'Speichert Aufnahme …' : 'Aufnahme stoppen'}
        </button>
      ) : (
        <button
          aria-label={
            recorderState === 'error'
              ? 'Aufnahme erneut versuchen'
              : 'Aufnahme starten'
          }
          className="audio-recorder__start"
          disabled={recorderState === 'requesting'}
          onClick={startRecording}
          type="button"
        >
          <span className="audio-recorder__microphone" aria-hidden="true">⌁</span>
          <span>
            {recorderState === 'error'
              ? 'Aufnahme erneut versuchen'
              : 'Aufnahme starten'}
          </span>
          <span className="audio-recorder__button-hint">
            {recorderState === 'requesting'
              ? 'Mikrofon wird geöffnet'
              : recorderState === 'error'
                ? 'Einstellungen prüfen und erneut antippen'
                : 'Zum Sprechen antippen'}
          </span>
        </button>
      )}

      {recorderState === 'recorded' &&
        audioBlob &&
        transcriptionState.kind !== 'error' && (
        <button
          className="audio-recorder__remove"
          onClick={removeRecording}
          type="button"
        >
          Aufnahme verwerfen
        </button>
      )}
    </section>
  )
}
