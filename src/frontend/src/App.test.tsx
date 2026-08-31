import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'

function startNewProcess() {
  return userEvent.setup()
}

function getSummarySection(label: string) {
  const section = screen.getByText(label, { selector: 'p' }).closest('section')

  if (!section) {
    throw new Error(`Zusammenfassung für ${label} nicht gefunden.`)
  }

  return section
}

describe('manueller Phase-3-Workflow', () => {
  beforeEach(() => {
    window.location.hash = ''
  })

  it('erhält Reifenwechsel-Daten über Übersicht und Bearbeitung bis zur Bestätigung', async () => {
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Reifenwechsel' }))

    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    fireEvent.change(screen.getByLabelText(/Hersteller/), {
      target: { value: 'Continental' },
    })
    fireEvent.change(screen.getByLabelText(/Modell/), {
      target: { value: 'WinterContact TS 870' },
    })

    expect(screen.getByLabelText(/Kennzeichen/)).toHaveValue('CW-AB 123')

    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    expect(screen.getByRole('heading', { name: 'Übersicht' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'CW-AB 123' })).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Montierter Reifensatz' }),
    ).toBeVisible()

    const tireSection = getSummarySection('Reifendaten')
    await user.click(
      within(tireSection).getByRole('button', { name: 'Bearbeiten' }),
    )
    fireEvent.change(screen.getByLabelText(/Modell/), {
      target: { value: 'WinterContact TS 870 P' },
    })
    await user.click(screen.getByRole('button', { name: 'Fertig' }))

    expect(screen.getByText('WinterContact TS 870 P')).toBeVisible()
    expect(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    ).toBeEnabled()

    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    )

    expect(screen.getByRole('heading', { name: 'Alles erledigt.' })).toBeVisible()
    expect(
      screen.getByText(/reifenwechsel für CW-AB 123 wurde lokal als bestätigt/i),
    ).toBeVisible()
  })

  it('blockiert eine fehlerhafte Einlagerung und bestätigt sie nach Korrektur', async () => {
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))

    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'not a plate' },
    })
    fireEvent.change(screen.getByLabelText('Breite'), {
      target: { value: '100' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    expect(
      screen.getByRole('heading', { name: 'Vorgang kann nicht bestätigt werden' }),
    ).toBeVisible()
    expect(screen.getByText('Reifenbreite:')).toBeVisible()
    expect(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    ).toBeDisabled()
    expect(
      screen.getByRole('heading', { name: 'Einzulagernder Reifensatz' }),
    ).toBeVisible()

    const plateSection = getSummarySection('Kennzeichen')
    await user.click(
      within(plateSection).getByRole('button', { name: 'Bearbeiten' }),
    )
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 987' },
    })
    await user.click(screen.getByRole('button', { name: 'Fertig' }))

    const tireSection = getSummarySection('Reifendaten')
    await user.click(
      within(tireSection).getByRole('button', { name: 'Bearbeiten' }),
    )
    fireEvent.change(screen.getByLabelText('Breite (mm)'), {
      target: { value: '205' },
    })
    await user.click(screen.getByRole('button', { name: 'Fertig' }))

    expect(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    ).toBeEnabled()

    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen/i }),
    )

    expect(
      screen.getByText(/einlagerung für CW-AB 987 wurde lokal als bestätigt/i),
    ).toBeVisible()
  })
})
