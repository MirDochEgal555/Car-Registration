import { useEffect, useState } from 'react'
import { MechanicStartPage } from './pages/MechanicStartPage'
import {
  type ServiceProtocolId,
  serviceProtocols,
} from './types/serviceProtocol'
import type {
  TireConditionType,
  TireSetDraft,
  TireSetRole,
  TireType,
  WorkshopProcess,
  WorkshopTireCondition,
  WorkshopTireInspection,
} from './types/workshopProcess'
import {
  getLicensePlateError,
  normalizeLicensePlate,
} from './utils/licensePlate'

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
    const tireSetRole = getInitialTireSetRole(serviceType)

    setWorkshopProcess({
      serviceType,
      status: 'draft',
      licensePlate: '',
      tireSets: [
        {
          role: tireSetRole,
          tireSet: {},
        },
      ],
      tireInspections: [
        {
          tireSetRole,
        },
      ],
      conditions: [
        {
          tireSetRole,
          position: 'all',
        },
      ],
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

  const licensePlateError = getLicensePlateError(workshopProcess.licensePlate)

  const updateLicensePlate = (value: string) => {
    setWorkshopProcess((currentProcess) => {
      if (!currentProcess) {
        return currentProcess
      }

      return {
        ...currentProcess,
        licensePlate: normalizeLicensePlate(value),
      }
    })
  }

  const updateTireSet = (changes: Partial<TireSetDraft>) => {
    setWorkshopProcess((currentProcess) => {
      if (!currentProcess) {
        return currentProcess
      }

      return {
        ...currentProcess,
        tireSets: currentProcess.tireSets.map((entry, index) =>
          index === 0
            ? {
                ...entry,
                tireSet: {
                  ...entry.tireSet,
                  ...changes,
                },
              }
            : entry,
        ),
      }
    })
  }

  const updateTireInspection = (changes: Partial<WorkshopTireInspection>) => {
    setWorkshopProcess((currentProcess) => {
      if (!currentProcess) {
        return currentProcess
      }

      return {
        ...currentProcess,
        tireInspections: currentProcess.tireInspections.map((inspection, index) =>
          index === 0 ? { ...inspection, ...changes } : inspection,
        ),
      }
    })
  }

  const updateTireCondition = (changes: Partial<WorkshopTireCondition>) => {
    setWorkshopProcess((currentProcess) => {
      if (!currentProcess) {
        return currentProcess
      }

      return {
        ...currentProcess,
        conditions: currentProcess.conditions.map((condition, index) =>
          index === 0 ? { ...condition, ...changes } : condition,
        ),
      }
    })
  }

  const tireSet = workshopProcess.tireSets[0]?.tireSet
  const tireInspection = workshopProcess.tireInspections[0]
  const tireCondition = workshopProcess.conditions[0]

  return (
    <main className="workshop-view">
      <AppHeader onHome={() => navigate('/')} />
      <section className="workshop-view__content" aria-labelledby="page-title">
        <p className="workshop-view__eyebrow">Neue Erfassung</p>
        <div className="selection-confirmation" aria-hidden="true">
          {protocol.icon}
        </div>
        <h1 id="page-title">Reifendaten erfassen</h1>
        <p className="workshop-view__intro">
          Erfasse den Reifensatz direkt am Fahrzeug. Die Angaben bleiben lokal im
          Vorgang gespeichert.
        </p>

        <div className="capture-context" aria-label="Gewählter Vorgang">
          <span aria-hidden="true">{protocol.icon}</span>
          {protocol.title}
        </div>

        <label className="license-plate-field" htmlFor="license-plate">
          <span className="license-plate-field__label">
            Kennzeichen <span className="field-status field-status--required">Pflicht</span>
          </span>
          <input
            aria-describedby={
              licensePlateError
                ? 'license-plate-hint license-plate-error'
                : 'license-plate-hint'
            }
            aria-invalid={licensePlateError ? true : undefined}
            autoCapitalize="characters"
            autoComplete="off"
            className="license-plate-field__input"
            id="license-plate"
            inputMode="text"
            onChange={(event) => updateLicensePlate(event.target.value)}
            placeholder="z. B. CW-AB 123"
            spellCheck={false}
            type="text"
            value={workshopProcess.licensePlate}
          />
          <span className="license-plate-field__hint" id="license-plate-hint">
            Leerzeichen und Bindestriche werden automatisch vereinheitlicht.
          </span>
        </label>

        {licensePlateError ? (
          <p className="field-message field-message--error" id="license-plate-error" role="alert">
            {licensePlateError}
          </p>
        ) : (
          <p className="field-message field-message--success" role="status">
            Kennzeichen ist im Vorgang gespeichert.
          </p>
        )}

        <section className="tire-capture" aria-labelledby="tire-data-title">
          <div className="tire-capture__heading">
            <div>
              <h2 id="tire-data-title">Reifensatz</h2>
              <p>
                Alle folgenden Reifenangaben sind im aktuellen Datenmodell optional.
              </p>
            </div>
            <span className="field-status field-status--optional">Optional</span>
          </div>

          <div className="tire-capture__grid">
            <label className="workshop-field" htmlFor="tire-type">
              <span>Reifenart <span className="field-status field-status--optional">Optional</span></span>
              <select
                id="tire-type"
                onChange={(event) =>
                  updateTireSet({
                    tireType: valueOrUndefined<TireType>(event.target.value),
                  })
                }
                value={tireSet?.tireType ?? ''}
              >
                <option value="">Bitte auswählen</option>
                <option value="summer">Sommerreifen</option>
                <option value="winter">Winterreifen</option>
                <option value="all_season">Ganzjahresreifen</option>
                <option value="unknown">Nicht bekannt</option>
              </select>
            </label>

            <fieldset className="tire-size-field">
              <legend>
                Reifengröße <span className="field-status field-status--optional">Optional</span>
              </legend>
              <div className="tire-size-field__inputs">
                <label htmlFor="tire-width">
                  <span>Breite</span>
                  <input
                    id="tire-width"
                    inputMode="numeric"
                    max="405"
                    min="125"
                    onChange={(event) =>
                      updateTireSet({ widthMm: numberOrUndefined(event.target.value) })
                    }
                    placeholder="205"
                    type="number"
                    value={tireSet?.widthMm ?? ''}
                  />
                </label>
                <span className="tire-size-field__separator" aria-hidden="true">/</span>
                <label htmlFor="tire-aspect-ratio">
                  <span>Querschnitt</span>
                  <input
                    id="tire-aspect-ratio"
                    inputMode="numeric"
                    max="95"
                    min="20"
                    onChange={(event) =>
                      updateTireSet({
                        aspectRatio: numberOrUndefined(event.target.value),
                      })
                    }
                    placeholder="55"
                    type="number"
                    value={tireSet?.aspectRatio ?? ''}
                  />
                </label>
                <span className="tire-size-field__r" aria-hidden="true">R</span>
                <label htmlFor="tire-rim-diameter">
                  <span>Felge in Zoll</span>
                  <input
                    id="tire-rim-diameter"
                    inputMode="numeric"
                    max="24"
                    min="10"
                    onChange={(event) =>
                      updateTireSet({
                        rimDiameterInch: numberOrUndefined(event.target.value),
                      })
                    }
                    placeholder="16"
                    type="number"
                    value={tireSet?.rimDiameterInch ?? ''}
                  />
                </label>
              </div>
            </fieldset>

            <label className="workshop-field" htmlFor="tire-manufacturer">
              <span>Hersteller <span className="field-status field-status--optional">Optional</span></span>
              <input
                autoComplete="off"
                id="tire-manufacturer"
                onChange={(event) => updateTireSet({ manufacturer: event.target.value || undefined })}
                placeholder="z. B. Continental"
                type="text"
                value={tireSet?.manufacturer ?? ''}
              />
            </label>

            <label className="workshop-field" htmlFor="tire-model">
              <span>Modell <span className="field-status field-status--optional">Optional</span></span>
              <input
                autoComplete="off"
                id="tire-model"
                onChange={(event) => updateTireSet({ model: event.target.value || undefined })}
                placeholder="z. B. WinterContact TS 870"
                type="text"
                value={tireSet?.model ?? ''}
              />
            </label>

            <label className="workshop-field" htmlFor="tire-quantity">
              <span>Menge <span className="field-status field-status--optional">Optional</span></span>
              <input
                id="tire-quantity"
                inputMode="numeric"
                min="1"
                onChange={(event) =>
                  updateTireSet({ quantity: numberOrUndefined(event.target.value) })
                }
                placeholder="4"
                type="number"
                value={tireSet?.quantity ?? ''}
              />
            </label>
          </div>

          <fieldset className="tread-depth-field">
            <legend>
              Profiltiefe <span className="field-status field-status--optional">Optional</span>
            </legend>
            <div className="tread-depth-field__inputs">
              <label htmlFor="tread-front">
                <span>Vorne</span>
                <div className="input-with-unit">
                  <input
                    id="tread-front"
                    inputMode="decimal"
                    max="20"
                    min="0"
                    onChange={(event) =>
                      updateTireInspection({
                        treadFrontMm: numberOrUndefined(event.target.value),
                      })
                    }
                    placeholder="z. B. 6,5"
                    step="0.1"
                    type="number"
                    value={tireInspection?.treadFrontMm ?? ''}
                  />
                  <span aria-hidden="true">mm</span>
                </div>
              </label>
              <label htmlFor="tread-rear">
                <span>Hinten</span>
                <div className="input-with-unit">
                  <input
                    id="tread-rear"
                    inputMode="decimal"
                    max="20"
                    min="0"
                    onChange={(event) =>
                      updateTireInspection({
                        treadRearMm: numberOrUndefined(event.target.value),
                      })
                    }
                    placeholder="z. B. 5,0"
                    step="0.1"
                    type="number"
                    value={tireInspection?.treadRearMm ?? ''}
                  />
                  <span aria-hidden="true">mm</span>
                </div>
              </label>
            </div>
          </fieldset>

          <div className="tire-capture__grid tire-capture__grid--final">
            <label className="workshop-field" htmlFor="tire-condition">
              <span>Zustand <span className="field-status field-status--optional">Optional</span></span>
              <select
                id="tire-condition"
                onChange={(event) =>
                  updateTireCondition({
                    condition: valueOrUndefined<TireConditionType>(event.target.value),
                  })
                }
                value={tireCondition?.condition ?? ''}
              >
                <option value="">Bitte auswählen</option>
                <option value="ok">Ohne Beanstandung</option>
                <option value="worn">Abgefahren</option>
                <option value="uneven_wear">Ungleichmäßig abgefahren</option>
                <option value="inner_wear">Innen abgefahren</option>
                <option value="outer_wear">Außen abgefahren</option>
                <option value="damaged">Beschädigt</option>
                <option value="cracked">Rissig</option>
                <option value="foreign_object">Fremdkörper</option>
                <option value="low_tread">Profil zu niedrig</option>
                <option value="unknown">Nicht beurteilbar</option>
              </select>
            </label>

            <label className="workshop-field workshop-field--full" htmlFor="tire-notes">
              <span>Notizen <span className="field-status field-status--optional">Optional</span></span>
              <textarea
                id="tire-notes"
                onChange={(event) => updateTireSet({ notes: event.target.value || undefined })}
                placeholder="Besonderheiten zum Reifensatz"
                rows={4}
                value={tireSet?.notes ?? ''}
              />
            </label>
          </div>
        </section>

        <p className="field-message field-message--saved" role="status">
          Reifendaten werden direkt im lokalen Vorgang gespeichert.
        </p>

        <button className="text-button" onClick={() => navigate('/neu')} type="button">
          Andere Erfassung wählen
        </button>
      </section>
    </main>
  )
}

function getInitialTireSetRole(serviceType: ServiceProtocolId): TireSetRole {
  return serviceType === 'tire_storage' ? 'stored' : 'installed'
}

function numberOrUndefined(value: string): number | undefined {
  if (value === '') {
    return undefined
  }

  const number = Number(value)
  return Number.isFinite(number) ? number : undefined
}

function valueOrUndefined<T extends string>(value: string): T | undefined {
  return value === '' ? undefined : (value as T)
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
