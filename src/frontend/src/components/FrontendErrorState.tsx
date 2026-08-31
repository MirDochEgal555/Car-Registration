import { Component, type ReactNode } from 'react'
import type { FrontendErrorKind } from '../types/frontendError'

const errorStateContent: Record<
  FrontendErrorKind,
  { icon: string; title: string }
> = {
  required: { icon: '!', title: 'Pflichtfeld fehlt' },
  invalid: { icon: '!', title: 'Eingabe prüfen' },
  confirmation: { icon: '!', title: 'Vorgang kann nicht bestätigt werden' },
  unexpected: { icon: '!', title: 'Etwas ist schiefgelaufen' },
}

type FrontendErrorStateProps = {
  children?: ReactNode
  id?: string
  kind: FrontendErrorKind
  message: string
  compact?: boolean
  title?: string
}

/** Einheitliche, gut sichtbare Fehlermeldung für die Werkstattansicht. */
export function FrontendErrorState({
  children,
  compact = false,
  id,
  kind,
  message,
  title,
}: FrontendErrorStateProps) {
  const content = errorStateContent[kind]
  const isCritical = kind === 'confirmation' || kind === 'unexpected'

  return (
    <section
      aria-live={isCritical ? 'assertive' : 'polite'}
      className={`frontend-error-state frontend-error-state--${kind}${
        compact ? ' frontend-error-state--compact' : ''
      }`}
      id={id}
      role={isCritical ? 'alert' : 'status'}
    >
      <span className="frontend-error-state__icon" aria-hidden="true">
        {content.icon}
      </span>
      <div className="frontend-error-state__content">
        <h2>{title ?? content.title}</h2>
        <p>{message}</p>
        {children}
      </div>
    </section>
  )
}

type FrontendErrorBoundaryProps = {
  children: ReactNode
  onHome: () => void
  onResume: () => void
}

type FrontendErrorBoundaryState = {
  hasError: boolean
}

/**
 * Fängt unerwartete Darstellungsfehler ab, ohne den Vorgang im übergeordneten
 * App-Zustand zurückzusetzen.
 */
export class FrontendErrorBoundary extends Component<
  FrontendErrorBoundaryProps,
  FrontendErrorBoundaryState
> {
  state: FrontendErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): FrontendErrorBoundaryState {
    return { hasError: true }
  }

  private resume = () => {
    this.setState({ hasError: false }, this.props.onResume)
  }

  private goHome = () => {
    this.setState({ hasError: false }, this.props.onHome)
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <main className="workshop-view">
        <section
          className="workshop-view__content"
          aria-labelledby="frontend-error-page-title"
        >
          <p className="workshop-view__eyebrow">Hinweis</p>
          <h1 id="frontend-error-page-title">Ansicht wiederherstellen</h1>
          <FrontendErrorState
            kind="unexpected"
            message="Diese Ansicht konnte nicht geladen werden. Deine Eingaben bleiben erhalten."
          />
          <button
            className="primary-action frontend-error-state__action"
            onClick={this.resume}
            type="button"
          >
            <span className="primary-action__icon" aria-hidden="true">
              ↻
            </span>
            <span>Erfassung fortsetzen</span>
            <span className="primary-action__hint">
              Zurück zu deinen gespeicherten Eingaben
            </span>
          </button>
          <button className="text-button" onClick={this.goHome} type="button">
            Zur Startansicht
          </button>
        </section>
      </main>
    )
  }
}
