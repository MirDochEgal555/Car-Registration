# CarTech Frontend

Die Mechanikeransicht prüft und versendet bestätigte Vorgänge an die FastAPI.
Sie verwendet dabei den gemeinsamen `RegistrationDraft`-Vertrag, zeigt
Backend-Validierung direkt in der Übersicht und bietet bei einem gespeicherten
E-Mail-Fehler einen Retry an.

## Voraussetzungen

- Node.js `20.19+` oder `22.12+`
- npm

## Lokal starten

```bash
cd src/frontend
npm install
npm run dev
```

Die Startseite wird von Vite unter der im Terminal ausgegebenen lokalen Adresse
bereitgestellt, standardmäßig unter `http://localhost:5173/`. Der integrierte
Dev-Proxy leitet `/api` an FastAPI unter `http://127.0.0.1:8000` weiter; das
Backend muss daher parallel gestartet sein:

```bash
cd ../backend
uvicorn app.main:app --reload
```

Für ein separates Deployment kann `VITE_API_BASE_URL` gesetzt werden (etwa
`https://cartech.example`). Ohne Variable ruft das Frontend relativ `/api/v1`
auf. `VITE_MECHANIC_ID` überschreibt die vorläufige MVP-Mechaniker-ID; vor
einem Produktivbetrieb muss diese durch die authentifizierte Identität ersetzt
werden.

## Qualitätsprüfungen

```bash
npm run lint
npm run build
```

`build` führt zunächst die TypeScript-Prüfung aus und erstellt dann die
Produktionsdateien im ignorierten Ordner `dist/`.
