import { type FormEvent, type ReactNode, useEffect, useState } from 'react'

type SessionState = 'loading' | 'login' | 'authenticated' | 'unavailable'
const AUTH_API = '/api/v1/auth'

export function AppLogin({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>('loading')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void fetch(`${AUTH_API}/session`, { credentials: 'same-origin' })
      .then(async (response) => {
        if (!response.ok) throw new Error('session')
        return response.json() as Promise<{ authenticated: boolean }>
      })
      .then((session) => setState(session.authenticated ? 'authenticated' : 'login'))
      .catch(() => setState('unavailable'))
  }, [])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    try {
      const response = await fetch(`${AUTH_API}/login`, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (response.ok) {
        setPassword('')
        setState('authenticated')
        return
      }
    } catch {
      // The generic message avoids revealing whether the service or account exists.
    }
    setError('Benutzername oder Passwort ist nicht korrekt.')
  }

  if (state === 'authenticated') return <>{children}</>
  if (state === 'loading') return <main className="login-view">Zugang wird geprüft …</main>
  if (state === 'unavailable') return <main className="login-view">Der Anmeldedienst ist derzeit nicht erreichbar.</main>
  return (
    <main className="login-view">
      <form className="login-card" onSubmit={(event) => void submit(event)}>
        <p className="workshop-view__eyebrow">CarTech Werkstatt</p>
        <h1>Anmelden</h1>
        <p>Bitte melde dich an, um Fahrzeugdaten zu erfassen.</p>
        <label>Benutzername<input autoComplete="username" onChange={(event) => setUsername(event.target.value)} required value={username} /></label>
        <label>Passwort<input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} /></label>
        {error && <p className="login-card__error" role="alert">{error}</p>}
        <button className="primary-action" type="submit">Anmelden</button>
      </form>
    </main>
  )
}
