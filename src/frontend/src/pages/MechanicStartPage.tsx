type MechanicStartPageProps = {
  hasDraft?: boolean
  onResume?: () => void
  onStart: () => void
}

export function MechanicStartPage({
  hasDraft = false,
  onResume,
  onStart,
}: MechanicStartPageProps) {
  return (
    <main className="workshop-view">
      <header className="app-header">
        <div className="app-header__brand" aria-label="CarTech">
          <span className="app-header__mark" aria-hidden="true">
            C
          </span>
          <span>CarTech</span>
        </div>
        <span className="app-header__context">Werkstatt</span>
      </header>

      <section className="workshop-view__content" aria-labelledby="page-title">
        <p className="workshop-view__eyebrow">Mechanikeransicht</p>
        <h1 id="page-title">Bereit für die Werkstatt.</h1>
        <p className="workshop-view__intro">
          Starte die Aufnahme und erfasse anschließend das Kennzeichen.
        </p>

        {hasDraft && onResume && (
          <button
            aria-label="Erfassung fortsetzen"
            className="primary-action"
            onClick={onResume}
            type="button"
          >
            <span className="primary-action__icon" aria-hidden="true">
              ↻
            </span>
            <span>Erfassung fortsetzen</span>
            <span className="primary-action__hint">
              Deine aktuellen Angaben bleiben erhalten
            </span>
          </button>
        )}

        <button
          className={hasDraft ? 'secondary-button' : 'primary-action'}
          onClick={onStart}
          type="button"
        >
          {hasDraft ? (
            'Neue Aufnahme beginnen'
          ) : (
            <>
              <span className="primary-action__icon" aria-hidden="true">
                ●
              </span>
              <span>Aufnahme starten</span>
              <span className="primary-action__hint">Transkript und Kennzeichen erfassen</span>
            </>
          )}
        </button>
      </section>
    </main>
  )
}
