import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
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

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function validRegistration(licensePlate: string) {
  return {
    valid: true,
    review_required: false,
    issues: [],
    registration: { vehicle: { license_plate: licensePlate } },
  }
}

function emailSent() {
  return {
    registration_id: 'c2feb07e-4854-4ef8-9e8a-14d8468df624',
    status: 'email_sent',
    recipient: 'office@example.com',
    attempt_count: 1,
    submitted_at: '2026-08-31T10:00:00Z',
  }
}

describe('Mechaniker → FastAPI → E-Mail-Workflow', () => {
  beforeEach(() => {
    window.location.hash = ''
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('mappt einen Reifenwechsel, prüft ihn und übergibt ihn an die Büro-E-Mail', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 123')))
      .mockResolvedValueOnce(response(emailSent()))
    vi.stubGlobal('fetch', fetchMock)
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
    await user.click(screen.getByLabelText('Ja'))
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )

    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('heading', { name: 'Alles erledigt.' }),
    ).toBeVisible()
    expect(screen.getByText(/e-mail wurde an office@example.com übergeben/i)).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0]?.[0]).toContain('/api/v1/registrations/validate')
    expect(fetchMock.mock.calls[1]?.[0]).toContain('/api/v1/registrations/send')

    const sendPayload = JSON.parse(
      String((fetchMock.mock.calls[1]?.[1] as RequestInit).body),
    )
    expect(sendPayload).toMatchObject({
      service_type: 'tire_change',
      mechanic_confirmed: true,
      vehicle: { license_plate: 'CW-AB 123' },
      tire_sets: [{ role: 'installed', tire_set: { manufacturer: 'Continental' } }],
      tire_change_details: { wheel_change_performed: true },
    })
  })

  it('zeigt Backend-Validierung an, ohne einen ungültigen Vorgang zu versenden', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      response({
        valid: false,
        review_required: true,
        registration: { vehicle: { license_plate: 'CW-AB 123' } },
        issues: [
          {
            field: 'tire_sets.0.tire_set.width_mm',
            code: 'implausible_value',
            message: 'Die Reifenbreite ist unplausibel.',
            status: 'invalid',
          },
        ],
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 123' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(await screen.findByRole('heading', { name: 'Backend-Validierung' })).toBeVisible()
    expect(screen.getByText('Reifenbreite:')).toBeVisible()
    expect(screen.getByText('Die Reifenbreite ist unplausibel.')).toBeVisible()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('bietet nach einem gespeicherten Versandfehler einen Retry an', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(validRegistration('CW-AB 987')))
      .mockResolvedValueOnce(
        response(
          {
            detail: {
              message: 'Der Versand ist fehlgeschlagen. Der Vorgang wurde gespeichert und kann erneut versendet werden.',
              delivery: {
                registration_id: 'c2feb07e-4854-4ef8-9e8a-14d8468df624',
                status: 'email_failed',
                attempt_count: 1,
                last_error: 'The office email could not be delivered.',
              },
            },
          },
          502,
        ),
      )
      .mockResolvedValueOnce(response({ ...emailSent(), attempt_count: 2 }))
    vi.stubGlobal('fetch', fetchMock)
    const user = startNewProcess()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /neue erfassung/i }))
    await user.click(screen.getByRole('button', { name: 'Einlagerung' }))
    fireEvent.change(screen.getByLabelText(/Kennzeichen/), {
      target: { value: 'cw ab 987' },
    })
    await user.click(
      screen.getByRole('button', { name: /aktuellen vorgang ansehen/i }),
    )
    await user.click(
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    )

    expect(
      await screen.findByRole('button', { name: 'Versand erneut versuchen' }),
    ).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Versand erneut versuchen' }))

    expect(
      await screen.findByText(/versand nach 2 versuchen erfolgreich/i),
    ).toBeVisible()
    expect(fetchMock.mock.calls[2]?.[0]).toMatch(/\/registrations\/[\w-]+\/retry$/)
  })

  it('blockiert eine fehlerhafte Einlagerung bis zur Korrektur', async () => {
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
      screen.getByRole('button', { name: /vorgang bestätigen.*senden/i }),
    ).toBeEnabled()
  })
})
