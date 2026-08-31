import { ProtocolCard } from '../components/ProtocolCard'
import { serviceProtocols } from '../types/serviceProtocol'

export function MechanicStartPage() {
  return (
    <main className="mechanic-start">
      <section className="mechanic-start__hero" aria-labelledby="page-title">
        <p className="eyebrow">CarTech · Mechanikeransicht</p>
        <h1 id="page-title">Neue Erfassung</h1>
        <p className="mechanic-start__intro">
          Wähle den passenden Vorgang. Die Aufnahme und Prüfung werden in einem
          folgenden Schritt ergänzt.
        </p>
      </section>

      <section aria-labelledby="protocol-title">
        <div className="section-heading">
          <p className="eyebrow">Schritt 1</p>
          <h2 id="protocol-title">Protokoll auswählen</h2>
        </div>
        <div className="protocol-list">
          {serviceProtocols.map((protocol) => (
            <ProtocolCard key={protocol.id} protocol={protocol} />
          ))}
        </div>
      </section>

      <aside className="implementation-note" aria-label="Entwicklungsstand">
        <span aria-hidden="true">i</span>
        <p>
          Frontend-Grundgerüst für Phase 3: Noch keine Aufnahme, Fachlogik oder
          Verbindung zum Backend.
        </p>
      </aside>
    </main>
  )
}
