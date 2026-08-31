import { type FormEvent, useEffect, useState } from 'react'
import { MechanicStartPage } from './pages/MechanicStartPage'
import {
  type ServiceProtocolId,
  type ServiceProtocol,
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
import {
  getWorkshopProcessValidationIssues,
  type WorkshopProcessValidationIssue,
} from './utils/workshopProcessValidation'

type Route = 'start' | 'selection' | 'capture' | 'overview' | 'success'

function getRoute(): Route {
  switch (window.location.hash) {
    case '#/neu':
      return 'selection'
    case '#/erfassung':
      return 'capture'
    case '#/uebersicht':
      return 'overview'
    case '#/bestaetigt':
      return 'success'
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

  if (
    (route !== 'capture' && route !== 'overview' && route !== 'success') ||
    !workshopProcess ||
    !protocol
  ) {
    return <MechanicStartPage onStart={() => navigate('/neu')} />
  }

  const licensePlateError = getLicensePlateError(workshopProcess.licensePlate)
  const confirmationIssues = getWorkshopProcessValidationIssues(workshopProcess)

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

  const confirmWorkshopProcess = () => {
    if (confirmationIssues.length > 0 || workshopProcess.status === 'confirmed') {
      return
    }

    setWorkshopProcess((currentProcess) => {
      if (
        !currentProcess ||
        currentProcess.status === 'confirmed' ||
        getWorkshopProcessValidationIssues(currentProcess).length > 0
      ) {
        return currentProcess
      }

      return { ...currentProcess, status: 'confirmed' }
    })
    navigate('/bestaetigt')
  }

  if (route === 'success') {
    if (workshopProcess.status !== 'confirmed') {
      return <MechanicStartPage onStart={() => navigate('/neu')} />
    }

    return (
      <ProcessConfirmedPage
        onHome={() => navigate('/')}
        onStartNewProcess={() => navigate('/neu')}
        process={workshopProcess}
        protocol={protocol}
      />
    )
  }

  if (route === 'overview') {
    return (
      <ProcessOverviewPage
        confirmationIssues={confirmationIssues}
        licensePlateError={licensePlateError}
        onConfirm={confirmWorkshopProcess}
        onEditCapture={() => navigate('/erfassung')}
        onHome={() => navigate('/')}
        onUpdateLicensePlate={updateLicensePlate}
        onUpdateTireCondition={updateTireCondition}
        onUpdateTireInspection={updateTireInspection}
        onUpdateTireSet={updateTireSet}
        process={workshopProcess}
        protocol={protocol}
        tireCondition={tireCondition}
        tireInspection={tireInspection}
        tireSet={tireSet}
      />
    )
  }

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

        <button
          className="secondary-button overview-action"
          onClick={() => navigate('/uebersicht')}
          type="button"
        >
          Aktuellen Vorgang ansehen
        </button>

        <button className="text-button" onClick={() => navigate('/neu')} type="button">
          Andere Erfassung wählen
        </button>
      </section>
    </main>
  )
}

type ProcessOverviewPageProps = {
  confirmationIssues: WorkshopProcessValidationIssue[]
  licensePlateError: string | null
  onConfirm: () => void
  onEditCapture: () => void
  onHome: () => void
  onUpdateLicensePlate: (value: string) => void
  onUpdateTireCondition: (changes: Partial<WorkshopTireCondition>) => void
  onUpdateTireInspection: (changes: Partial<WorkshopTireInspection>) => void
  onUpdateTireSet: (changes: Partial<TireSetDraft>) => void
  process: WorkshopProcess
  protocol: ServiceProtocol
  tireCondition: WorkshopTireCondition | undefined
  tireInspection: WorkshopTireInspection | undefined
  tireSet: TireSetDraft | undefined
}

function ProcessOverviewPage({
  confirmationIssues,
  licensePlateError,
  onConfirm,
  onEditCapture,
  onHome,
  onUpdateLicensePlate,
  onUpdateTireCondition,
  onUpdateTireInspection,
  onUpdateTireSet,
  process,
  protocol,
  tireCondition,
  tireInspection,
  tireSet,
}: ProcessOverviewPageProps) {
  const [editingSection, setEditingSection] = useState<'plate' | 'tires' | null>(
    null,
  )
  const isEditing = (section: 'plate' | 'tires') =>
    editingSection === section
  const closeEditor = () => setEditingSection(null)
  const finishEditing = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (
      !event.currentTarget.reportValidity() ||
      (editingSection === 'plate' && licensePlateError)
    ) {
      return
    }

    closeEditor()
  }

  return (
    <main className="workshop-view">
      <AppHeader onHome={onHome} />
      <section
        className="workshop-view__content workshop-view__content--overview"
        aria-labelledby="page-title"
      >
        <p className="workshop-view__eyebrow">Aktueller Vorgang</p>
        <h1 id="page-title">Übersicht</h1>
        <p className="workshop-view__intro">
          Alle erfassten Angaben auf einen Blick. Tippe auf „Bearbeiten“, um etwas
          direkt zu korrigieren.
        </p>

        {confirmationIssues.length > 0 && (
          <section
            className="confirmation-errors"
            aria-labelledby="confirmation-errors-title"
            role="alert"
          >
            <h2 id="confirmation-errors-title">Vorgang noch nicht bestätigbar</h2>
            <p>
              Bitte korrigiere die folgenden fehlenden oder ungültigen Angaben.
            </p>
            <ul>
              {confirmationIssues.map((issue) => (
                <li key={`${issue.field}-${issue.message}`}>
                  <strong>{issue.field}:</strong> {issue.message}
                </li>
              ))}
            </ul>
          </section>
        )}

        <div className="summary-stack">
          <section className="summary-card" aria-labelledby="summary-service-title">
            <div className="summary-card__heading">
              <div>
                <p className="summary-card__label">Vorgangstyp</p>
                <h2 id="summary-service-title">
                  <span aria-hidden="true">{protocol.icon}</span> {protocol.title}
                </h2>
              </div>
            </div>
          </section>

          <section className="summary-card" aria-labelledby="summary-plate-title">
            <div className="summary-card__heading">
              <div>
                <p className="summary-card__label">Kennzeichen</p>
                <h2
                  className={`summary-card__plate${
                    process.licensePlate ? '' : ' summary-card__value--missing'
                  }`}
                  id="summary-plate-title"
                >
                  {process.licensePlate || 'Nicht erfasst'}
                </h2>
              </div>
              <button
                aria-expanded={isEditing('plate')}
                className="summary-card__edit"
                onClick={() =>
                  setEditingSection(isEditing('plate') ? null : 'plate')
                }
                type="button"
              >
                Bearbeiten
              </button>
            </div>

            {isEditing('plate') && (
              <form className="summary-editor" onSubmit={finishEditing}>
                <label className="summary-editor__field" htmlFor="overview-license-plate">
                  <span>Kennzeichen</span>
                  <input
                    aria-describedby="overview-license-plate-hint"
                    aria-invalid={licensePlateError ? true : undefined}
                    autoCapitalize="characters"
                    autoComplete="off"
                    id="overview-license-plate"
                    onChange={(event) => onUpdateLicensePlate(event.target.value)}
                    pattern="[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\\s\\d{1,4}[A-Z]?"
                    placeholder="z. B. CW-AB 123"
                    required
                    spellCheck={false}
                    type="text"
                    value={process.licensePlate}
                  />
                </label>
                <p
                  className={
                    licensePlateError
                      ? 'summary-editor__message summary-editor__message--error'
                      : 'summary-editor__message'
                  }
                  id="overview-license-plate-hint"
                >
                  {licensePlateError ?? 'Kennzeichen ist im Vorgang gespeichert.'}
                </p>
                <button className="summary-editor__done" type="submit">
                  Fertig
                </button>
              </form>
            )}
          </section>

          <section className="summary-card" aria-labelledby="summary-tires-title">
            <div className="summary-card__heading">
              <div>
                <p className="summary-card__label">Reifendaten</p>
                <h2 id="summary-tires-title">
                  {tireSetRoleLabel(process.tireSets[0]?.role)}
                </h2>
              </div>
              <button
                aria-expanded={isEditing('tires')}
                className="summary-card__edit"
                onClick={() =>
                  setEditingSection(isEditing('tires') ? null : 'tires')
                }
                type="button"
              >
                Bearbeiten
              </button>
            </div>

            <dl className="summary-data-grid">
              <SummaryItem
                label="Reifenart"
                missing={!tireSet?.tireType}
                value={tireTypeLabel(tireSet?.tireType)}
              />
              <SummaryItem
                label="Reifengröße"
                missing={
                  tireSet?.widthMm === undefined &&
                  tireSet?.aspectRatio === undefined &&
                  tireSet?.rimDiameterInch === undefined
                }
                value={formatTireSize(tireSet)}
              />
              <SummaryItem
                label="Hersteller"
                missing={!tireSet?.manufacturer}
                value={tireSet?.manufacturer || 'Nicht erfasst'}
              />
              <SummaryItem
                label="Modell"
                missing={!tireSet?.model}
                value={tireSet?.model || 'Nicht erfasst'}
              />
              <SummaryItem
                label="Menge"
                missing={tireSet?.quantity === undefined}
                value={
                  tireSet?.quantity === undefined
                    ? 'Nicht erfasst'
                    : `${tireSet.quantity} Reifen`
                }
              />
              <SummaryItem
                label="Profiltiefe vorne"
                missing={tireInspection?.treadFrontMm === undefined}
                value={formatMillimeters(tireInspection?.treadFrontMm)}
              />
              <SummaryItem
                label="Profiltiefe hinten"
                missing={tireInspection?.treadRearMm === undefined}
                value={formatMillimeters(tireInspection?.treadRearMm)}
              />
              <SummaryItem
                label="Zustand"
                missing={!tireCondition?.condition}
                value={tireConditionLabel(tireCondition?.condition)}
              />
              <SummaryItem
                fullWidth
                label="Notizen"
                missing={!tireSet?.notes}
                value={tireSet?.notes || 'Nicht erfasst'}
              />
            </dl>

            {isEditing('tires') && (
              <form
                aria-label="Reifendaten bearbeiten"
                className="summary-editor"
                onSubmit={finishEditing}
              >
                <div className="summary-editor__grid">
                  <label className="summary-editor__field" htmlFor="overview-tire-type">
                    <span>Reifenart</span>
                    <select
                      id="overview-tire-type"
                      onChange={(event) =>
                        onUpdateTireSet({
                          tireType: valueOrUndefined<TireType>(event.target.value),
                        })
                      }
                      value={tireSet?.tireType ?? ''}
                    >
                      <option value="">Nicht erfasst</option>
                      <option value="summer">Sommerreifen</option>
                      <option value="winter">Winterreifen</option>
                      <option value="all_season">Ganzjahresreifen</option>
                      <option value="unknown">Nicht bekannt</option>
                    </select>
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-quantity">
                    <span>Menge</span>
                    <input
                      id="overview-tire-quantity"
                      inputMode="numeric"
                      min="1"
                      onChange={(event) =>
                        onUpdateTireSet({ quantity: numberOrUndefined(event.target.value) })
                      }
                      type="number"
                      value={tireSet?.quantity ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-width">
                    <span>Breite (mm)</span>
                    <input
                      id="overview-tire-width"
                      inputMode="numeric"
                      max="405"
                      min="125"
                      onChange={(event) =>
                        onUpdateTireSet({ widthMm: numberOrUndefined(event.target.value) })
                      }
                      type="number"
                      value={tireSet?.widthMm ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-aspect-ratio">
                    <span>Querschnitt</span>
                    <input
                      id="overview-tire-aspect-ratio"
                      inputMode="numeric"
                      max="95"
                      min="20"
                      onChange={(event) =>
                        onUpdateTireSet({
                          aspectRatio: numberOrUndefined(event.target.value),
                        })
                      }
                      type="number"
                      value={tireSet?.aspectRatio ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-rim-diameter">
                    <span>Felge (Zoll)</span>
                    <input
                      id="overview-tire-rim-diameter"
                      inputMode="numeric"
                      max="24"
                      min="10"
                      onChange={(event) =>
                        onUpdateTireSet({
                          rimDiameterInch: numberOrUndefined(event.target.value),
                        })
                      }
                      type="number"
                      value={tireSet?.rimDiameterInch ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-manufacturer">
                    <span>Hersteller</span>
                    <input
                      autoComplete="off"
                      id="overview-tire-manufacturer"
                      onChange={(event) =>
                        onUpdateTireSet({ manufacturer: event.target.value || undefined })
                      }
                      type="text"
                      value={tireSet?.manufacturer ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-model">
                    <span>Modell</span>
                    <input
                      autoComplete="off"
                      id="overview-tire-model"
                      onChange={(event) =>
                        onUpdateTireSet({ model: event.target.value || undefined })
                      }
                      type="text"
                      value={tireSet?.model ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tread-front">
                    <span>Profil vorne (mm)</span>
                    <input
                      id="overview-tread-front"
                      inputMode="decimal"
                      max="20"
                      min="0"
                      onChange={(event) =>
                        onUpdateTireInspection({
                          treadFrontMm: numberOrUndefined(event.target.value),
                        })
                      }
                      step="0.1"
                      type="number"
                      value={tireInspection?.treadFrontMm ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tread-rear">
                    <span>Profil hinten (mm)</span>
                    <input
                      id="overview-tread-rear"
                      inputMode="decimal"
                      max="20"
                      min="0"
                      onChange={(event) =>
                        onUpdateTireInspection({
                          treadRearMm: numberOrUndefined(event.target.value),
                        })
                      }
                      step="0.1"
                      type="number"
                      value={tireInspection?.treadRearMm ?? ''}
                    />
                  </label>
                  <label className="summary-editor__field" htmlFor="overview-tire-condition">
                    <span>Zustand</span>
                    <select
                      id="overview-tire-condition"
                      onChange={(event) =>
                        onUpdateTireCondition({
                          condition: valueOrUndefined<TireConditionType>(event.target.value),
                        })
                      }
                      value={tireCondition?.condition ?? ''}
                    >
                      <option value="">Nicht erfasst</option>
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
                  <label
                    className="summary-editor__field summary-editor__field--full"
                    htmlFor="overview-tire-notes"
                  >
                    <span>Notizen</span>
                    <textarea
                      id="overview-tire-notes"
                      onChange={(event) =>
                        onUpdateTireSet({ notes: event.target.value || undefined })
                      }
                      rows={3}
                      value={tireSet?.notes ?? ''}
                    />
                  </label>
                </div>
                <button className="summary-editor__done" type="submit">
                  Fertig
                </button>
              </form>
            )}
          </section>
        </div>

        <button
          aria-describedby={
            confirmationIssues.length > 0 ? 'confirmation-errors-title' : undefined
          }
          className="primary-action confirmation-action"
          disabled={confirmationIssues.length > 0 || process.status === 'confirmed'}
          onClick={onConfirm}
          type="button"
        >
          <span className="primary-action__icon" aria-hidden="true">✓</span>
          <span>Vorgang bestätigen</span>
          <span className="primary-action__hint">
            {confirmationIssues.length > 0
              ? 'Erforderliche Angaben ergänzen oder korrigieren'
              : 'Bestätigt den Vorgang lokal – es wird noch nichts übermittelt'}
          </span>
        </button>

        <button className="secondary-button overview-action" onClick={onEditCapture} type="button">
          Zur Erfassung zurück
        </button>
      </section>
    </main>
  )
}

type ProcessConfirmedPageProps = {
  onHome: () => void
  onStartNewProcess: () => void
  process: WorkshopProcess
  protocol: ServiceProtocol
}

function ProcessConfirmedPage({
  onHome,
  onStartNewProcess,
  process,
  protocol,
}: ProcessConfirmedPageProps) {
  return (
    <main className="workshop-view">
      <AppHeader onHome={onHome} />
      <section className="workshop-view__content confirmation-success" aria-labelledby="page-title">
        <div className="confirmation-success__icon" aria-hidden="true">✓</div>
        <p className="workshop-view__eyebrow">Vorgang bestätigt</p>
        <h1 id="page-title">Alles erledigt.</h1>
        <p className="workshop-view__intro">
          {protocol.title} für {process.licensePlate} wurde lokal als bestätigt
          markiert.
        </p>
        <p className="confirmation-success__notice">
          Es wurde noch keine Übermittlung an das Backend ausgelöst.
        </p>
        <button className="primary-action confirmation-action" onClick={onStartNewProcess} type="button">
          <span className="primary-action__icon" aria-hidden="true">+</span>
          <span>Neuen Vorgang erfassen</span>
          <span className="primary-action__hint">Zur Auswahl der Vorgangsart</span>
        </button>
      </section>
    </main>
  )
}

type SummaryItemProps = {
  fullWidth?: boolean
  label: string
  missing: boolean
  value: string
}

function SummaryItem({ fullWidth = false, label, missing, value }: SummaryItemProps) {
  return (
    <div className={fullWidth ? 'summary-data-grid__item summary-data-grid__item--full' : 'summary-data-grid__item'}>
      <dt>{label}</dt>
      <dd className={missing ? 'summary-card__value--missing' : undefined}>{value}</dd>
    </div>
  )
}

function tireSetRoleLabel(role: TireSetRole | undefined): string {
  if (role === 'installed') {
    return 'Montierter Reifensatz'
  }

  if (role === 'stored') {
    return 'Einzulagernder Reifensatz'
  }

  if (role === 'removed') {
    return 'Demontierter Reifensatz'
  }

  return 'Reifensatz'
}

function tireTypeLabel(tireType: TireType | undefined): string {
  const labels: Record<TireType, string> = {
    summer: 'Sommerreifen',
    winter: 'Winterreifen',
    all_season: 'Ganzjahresreifen',
    unknown: 'Nicht bekannt',
  }

  return tireType ? labels[tireType] : 'Nicht erfasst'
}

function tireConditionLabel(condition: TireConditionType | undefined): string {
  const labels: Record<TireConditionType, string> = {
    ok: 'Ohne Beanstandung',
    worn: 'Abgefahren',
    uneven_wear: 'Ungleichmäßig abgefahren',
    inner_wear: 'Innen abgefahren',
    outer_wear: 'Außen abgefahren',
    damaged: 'Beschädigt',
    cracked: 'Rissig',
    foreign_object: 'Fremdkörper',
    low_tread: 'Profil zu niedrig',
    unknown: 'Nicht beurteilbar',
  }

  return condition ? labels[condition] : 'Nicht erfasst'
}

function formatTireSize(tireSet: TireSetDraft | undefined): string {
  if (
    tireSet?.widthMm === undefined &&
    tireSet?.aspectRatio === undefined &&
    tireSet?.rimDiameterInch === undefined
  ) {
    return 'Nicht erfasst'
  }

  const width = tireSet.widthMm ?? '–'
  const aspectRatio = tireSet.aspectRatio ?? '–'
  const diameter = tireSet.rimDiameterInch ?? '–'

  return `${width} / ${aspectRatio} R${diameter}`
}

function formatMillimeters(value: number | undefined): string {
  return value === undefined ? 'Nicht erfasst' : `${value.toLocaleString('de-DE')} mm`
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
