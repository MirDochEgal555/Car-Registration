# Fahrzeug- & Reifenerfassung für CarTech

Voice-first-MVP für die Werkstatt **CarTech** zur Erfassung von Fahrzeugen sowie zwei Werkstattprotokollen: **Reifenwechsel** und **Reifeneinlagerung**. Der Ablauf ist: **Mechaniker wählt das Protokoll → spricht → KI strukturiert Daten → Mechaniker bestätigt → Büro prüft → manuelle WERBAS-Übernahme**.

**Aktueller Stand: [Projektstatus](STATUS.md)**

## Projektstruktur

```text
documentation/  Fachliche und technische Vorgaben
src/
  frontend/     React/TypeScript-PWA für Mechaniker und Büro
  backend/      FastAPI-Service, KI-Extraktion und Datenzugriff
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
- [Regeln für die Sprach- und KI-Extraktion](documentation/EXTRACTION_RULES.md)
- [Extraktions-Testfälle](documentation/TEST_CASES.md)
- [Technologie-Stack und Kosten](documentation/TECH_STACK.md)
- [Projektzeitplan](documentation/TIMELINE.md)
- [Arbeitsdokumentation](Stunden.csv)

## Wichtige Regeln

- Nur ausdrücklich genannte Informationen übernehmen; fehlende oder unsichere Werte markieren, niemals erraten.
- Kundenzuordnung und finale Prüfung erfolgen ausschließlich im Büro.
- Der Vorgangsstatus beschreibt den Ablauf; Feldstatus und `review_required` beschreiben Unsicherheiten oder Validierungsbedarf.
- Im Reifenwechselprotokoll erhalten Reifensätze die Rolle `installed` oder `removed`; im Einlagerungsprotokoll die Rolle `stored`.
- Reale Audio-, Kunden- oder Fahrzeugdaten gehören nicht ins Repository; für Tests nur anonymisierte Fixtures verwenden.
