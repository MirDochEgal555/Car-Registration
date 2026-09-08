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
          Starte einen neuen Vorgang mit wenigen Berührungen.
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
            'Neue Erfassung beginnen'
          ) : (
            <>
              <span className="primary-action__icon" aria-hidden="true">
                +
              </span>
              <span>Neue Erfassung</span>
              <span className="primary-action__hint">Vorgang auswählen</span>
            </>
          )}
        </button>
      </section>
    </main>
  )
}
