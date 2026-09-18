# Lokal starten und testen

Diese Anleitung startet das CarTech-Frontend, das FastAPI-Backend und
optional einen lokalen SMTP-Testserver. Dafür sind drei getrennte Terminals
praktisch.

## Einmalig einrichten

```bash
cd "/Users/robin/VS Code/Car Registration CarTech/src/backend"
python3 -m pip install -e '.[dev]'

cd "/Users/robin/VS Code/Car Registration CarTech/src/frontend"
npm install
```

Lege anschließend `src/backend/.env` an. Die Datei enthält lokale Zugangsdaten
und darf nicht in Git eingecheckt werden. Als Ausgangspunkt dient
`src/backend/.env.example`.

Für Sprachaufnahme und KI-Extraktion werden mindestens diese Werte benötigt:

```env
CARTECH_OPENAI_API_KEY=sk-...
CARTECH_OPENAI_TRANSCRIPTION_MODEL=gpt-transcribe
CARTECH_OPENAI_EXTRACTION_MODEL=gpt-4o-mini
CARTECH_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Anwendung starten

### Terminal 1: Backend

```bash
cd "/Users/robin/VS Code/Car Registration CarTech/src/backend"
python3 -m uvicorn app.main:app --reload --env-file .env
```

Backend-Gesundheitscheck: <http://127.0.0.1:8000/api/v1/health>

### Terminal 2: Frontend

```bash
cd "/Users/robin/VS Code/Car Registration CarTech/src/frontend"
npm run dev
```

Die Anwendung öffnen: <http://localhost:5173>

Der Vite-Entwicklungsserver leitet `/api` automatisch an das Backend auf Port
8000 weiter. `VITE_API_BASE_URL` sollte für diesen lokalen Ablauf nicht gesetzt
sein.

## E-Mail-Versand ohne echte E-Mail testen

### Mailpit mit Browser-Vorschau (empfohlen)

Mailpit fängt Testmails ab und zeigt die HTML- und Textversion in einer lokalen
Web-Inbox an. Auf macOS ohne Docker kann es über Homebrew installiert werden:

```bash
brew install mailpit
mailpit
```

Falls der Python-SMTP-Debug-Server noch läuft, vorher mit `Ctrl+C` beenden,
weil Mailpit ebenfalls Port 1025 verwendet. Anschließend die Mailansicht unter
<http://localhost:8025> öffnen. Die SMTP-Konfiguration unten bleibt identisch.

### Terminal 3: lokaler SMTP-Debug-Server

macOS-Systempython 3.9 enthält einen einfachen SMTP-Debug-Server:

```bash
python3 -m smtpd -n -c DebuggingServer 127.0.0.1:1025
```

Er zeigt jede Mail im Terminal an, ohne sie extern zuzustellen. Ergänze dafür
in `src/backend/.env`:

```env
CARTECH_OFFICE_EMAIL=office@cartech.test
CARTECH_SMTP_HOST=127.0.0.1
CARTECH_SMTP_PORT=1025
CARTECH_SMTP_FROM=cartech@local.test
CARTECH_SMTP_USE_TLS=false
CARTECH_SMTP_USE_SSL=false
```

`CARTECH_SMTP_USERNAME` und `CARTECH_SMTP_PASSWORD` leer lassen oder entfernen.
Danach das Backend neu starten. In der App einen Vorgang erfassen, auf
**„Aktuellen Vorgang ansehen“** und anschließend auf **„Vorgang bestätigen &
senden“** klicken. Die Mail erscheint im SMTP-Terminal.

Für einen Retry-Test den SMTP-Debug-Server vor dem Versand mit `Ctrl+C`
beenden. Nach dem Versandfehler erneut starten und in der App **„Erneut senden“**
wählen.

## Prüfungen ausführen

### Backend-Tests

```bash
cd "/Users/robin/VS Code/Car Registration CarTech/src/backend"
python3 -m pytest -q
```

### Frontend-Tests, Lint und Produktions-Build

```bash
cd "/Users/robin/VS Code/Car Registration CarTech/src/frontend"
npm test -- --run
npm run lint
npm run build
```
