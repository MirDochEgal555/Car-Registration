# CarTech Frontend

Das Frontend ist bewusst vom FastAPI-Backend getrennt und bildet in Phase 3
nur den Einstieg der Mechanikeransicht ab. Es enthält keine API-Aufrufe,
Fachlogik oder KI-Anbindung.

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
bereitgestellt, standardmäßig unter `http://localhost:5173/`.

## Qualitätsprüfungen

```bash
npm run lint
npm run build
```

`build` führt zunächst die TypeScript-Prüfung aus und erstellt dann die
Produktionsdateien im ignorierten Ordner `dist/`.
