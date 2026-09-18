# Fahrzeug- & Reifenerfassung für CarTech

Voice-first-MVP für die Werkstatt **CarTech** zur Erfassung von Fahrzeugen sowie zwei Werkstattprotokollen: **Reifenwechsel** und **Reifeneinlagerung**. Das Backend stellt dafür die vollständige Pipeline **Transkript → KI‑Structured‑Output → Normalisierung → Validierung → `RegistrationDraft`** über `POST /api/v1/extractions` bereit. Die bestehende Mechanikeroberfläche kann Entwürfe weiterhin manuell prüfen und versenden; ihre automatische Anbindung an diesen neuen Endpunkt ist ein separater nächster Schritt.

**Aktueller Stand: [Projektstatus](STATUS.md)**

**Lokale Entwicklung und Tests: [Anleitung zum Starten](documentation/LOCAL_RUN.md)**

## Live-Demo für die Werkstatt

Die aktuelle Frontend-Ansicht ist unter [mirdochegal555.github.io/Car-Registration](https://mirdochegal555.github.io/Car-Registration/) erreichbar. Sie wird bei jedem Push auf `main` automatisch über GitHub Pages aktualisiert.

GitHub Pages stellt ausschließlich das statische Frontend bereit. Für Validierung, Versand und Statusabfragen muss das FastAPI-Backend separat öffentlich erreichbar sein und seine Basis-URL beim Build über `VITE_API_BASE_URL` hinterlegt werden.

Für KI-Extraktion benötigt das Backend zusätzlich einen OpenAI-API-Schlüssel und ein Modell mit Strict Structured Outputs; Details stehen im [Backend-README](src/backend/README.md).

## Projektstruktur

```text
documentation/  Fachliche und technische Vorgaben
src/
  frontend/     React/TypeScript-PWA für die Mechaniker-Erfassung
  backend/      FastAPI-Service, KI-Extraktion und E-Mail-Versand
data/
  raw/          Nicht versionierte Rohdaten, z. B. Audio (keine echten Kundendaten einchecken)
  processed/    Lokal erzeugte, aufbereitete Daten
  fixtures/     Anonymisierte Testdaten
tests/          Automatisierte Tests
```

## Dokumentation

- [Projektstatus](STATUS.md)
- [Projektziel und Leitprinzipien](documentation/PROJECT.md)
- [Benutzerabläufe für Mechaniker und Büro](documentation/USER_FLOW.md)
- [Datenmodell](documentation/DATA_MODEL.md)
- [Backend-Dokumentation und Kohärenzbewertung](documentation/BACKEND.md)
- [Regeln für die Sprach- und KI-Extraktion](documentation/EXTRACTION_RULES.md)
- [Extraktions-Testfälle](documentation/TEST_CASES.md)
- [Technologie-Stack und Kosten](documentation/TECH_STACK.md)
- [Projektzeitplan](documentation/TIMELINE.md)
- [Arbeitsdokumentation](Stunden.csv)

## Wichtige Regeln

- Nur ausdrücklich genannte Informationen übernehmen; fehlende oder unsichere Werte markieren, niemals erraten.
- Kundenzuordnung und finale Prüfung erfolgen ausschließlich im Büro.
- Der Vorgangsstatus beschreibt den Ablauf; Feldstatus und `review_required` beschreiben Unsicherheiten oder Validierungsbedarf.
- Die KI-Extraktion ergänzt keine Werte. Nicht leere, aber vollständig unbrauchbare Transkripte werden mit `notes: null`, `field_status: uncertain` und `review_required: true` an die Prüfung übergeben.
- Jeder abgesendete Vorgang erzeugt eine E-Mail mit dem vollständigen strukturierten Protokoll, Kennzeichen, Zeitpunkt sowie klar markierten unsicheren oder unplausiblen Feldern.
- Im Reifenwechselprotokoll erhalten Reifensätze die Rolle `installed` oder `removed`; im Einlagerungsprotokoll die Rolle `stored`.
- WERBAS bleibt das führende Speichersystem. Im MVP gibt es keine direkte technische WERBAS-Integration; das Büro übernimmt die E-Mail-Inhalte manuell.
- Eine zentrale Speicherung und eine Büro-Inbox in der Web-App sind optionale spätere Erweiterungen.
- Reale Audio-, Kunden- oder Fahrzeugdaten gehören nicht ins Repository; für Tests nur anonymisierte Fixtures verwenden.
