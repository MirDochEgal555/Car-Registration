import { useEffect, useState } from 'react'
import { MechanicStartPage } from './pages/MechanicStartPage'
import {
  type ServiceProtocolId,
  serviceProtocols,
} from './types/serviceProtocol'
import type { WorkshopProcess } from './types/workshopProcess'

type Route = 'start' | 'selection' | 'capture'

function getRoute(): Route {
  switch (window.location.hash) {
    case '#/neu':
      return 'selection'
    case '#/erfassung':
      return 'capture'
    default:
      return 'start'
  }
}

function App() {
  const [route, setRoute] = useState<Route>(getRoute)
  const [workshopProcess, setWorkshopProcess] = useState<WorkshopProcess | null>(
    null,
  )

  useEffect(() => {
    const updateRoute = () => setRoute(getRoute())

    window.addEventListener('hashchange', updateRoute)
    return () => window.removeEventListener('hashchange', updateRoute)
  }, [])

  const navigate = (path: string) => {
    window.location.hash = path
  }

  const startWorkshopProcess = (serviceType: ServiceProtocolId) => {
    setWorkshopProcess({
      serviceType,
      status: 'draft',
    })
    navigate('/erfassung')
  }

  if (route === 'start') {
    return <MechanicStartPage onStart={() => navigate('/neu')} />
  }

  if (route === 'selection') {
    return (
      <main className="workshop-view">
        <AppHeader onHome={() => navigate('/')} />
        <section className="workshop-view__content" aria-labelledby="page-title">
          <p className="workshop-view__eyebrow">Neue Erfassung</p>
          <h1 id="page-title">Was wird gemacht?</h1>
          <p className="workshop-view__intro">
            Wähle den passenden Vorgang.
          </p>

          <div className="service-selection" aria-label="Vorgang auswählen">
            {serviceProtocols.map((protocol) => (
              <button
                className="service-selection__button"
                key={protocol.id}
                onClick={() => startWorkshopProcess(protocol.id)}
                type="button"
              >
                <span className="service-selection__icon" aria-hidden="true">
                  {protocol.icon}
                </span>
                <span>{protocol.title}</span>
                <span className="service-selection__arrow" aria-hidden="true">
                  →
                </span>
              </button>
            ))}
          </div>

          <button
            className="text-button"
            onClick={() => navigate('/')}
            type="button"
          >
            Zurück zur Startansicht
          </button>
        </section>
      </main>
    )
  }

  const protocol = serviceProtocols.find(
    (item) => item.id === workshopProcess?.serviceType,
  )

  if (route !== 'capture' || !workshopProcess || !protocol) {
    return <MechanicStartPage onStart={() => navigate('/neu')} />
  }

  return (
    <main className="workshop-view">
      <AppHeader onHome={() => navigate('/')} />
      <section className="workshop-view__content" aria-labelledby="page-title">
        <p className="workshop-view__eyebrow">Neue Erfassung</p>
        <div className="selection-confirmation" aria-hidden="true">
          {protocol.icon}
        </div>
        <h1 id="page-title">{protocol.title}</h1>
        <p className="workshop-view__intro">
          Der Vorgang wurde als Entwurf angelegt. Die Datenerfassung wird im
          nächsten Schritt ergänzt.
        </p>

        <button
          className="secondary-button"
          onClick={() => navigate('/neu')}
          type="button"
        >
          Andere Erfassung wählen
        </button>
      </section>
    </main>
  )
}

type AppHeaderProps = {
  onHome: () => void
}

function AppHeader({ onHome }: AppHeaderProps) {
  return (
    <header className="app-header">
      <button className="app-header__brand" onClick={onHome} type="button">
        <span className="app-header__mark" aria-hidden="true">
          C
        </span>
        <span>CarTech</span>
      </button>
      <span className="app-header__context">Werkstatt</span>
    </header>
  )
}

export default App
