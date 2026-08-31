# Projektstatus

**Stand: 31.08.2026**

## Repositoryzustand

- Branch: `main` auf Commit `340f8b7` (`Backend-Frontend Integration`)
- Überprüfter Ausgangszustand: Arbeitsbaum sauber; `main` entsprach `origin/main`
- Backend-Qualitätsprüfung: **62 Tests erfolgreich** (`python3 -m pytest`)
- Frontend-Qualitätsprüfung: **10 Tests erfolgreich**, ESLint und Produktions-Build erfolgreich (`npm test`, `npm run lint`, `npm run build`)

## Fertig

- MVP-Scope, Benutzerabläufe, Datenmodell, Extraktionsregeln, Testfälle und Zeitplan dokumentiert
- FastAPI-Backend mit versionierter API, Health-Endpoint und zentralen Datenmodellen umgesetzt
- Validierung vollständiger Vorgangsentwürfe inklusive Feldstatus (`missing`, `uncertain`, `invalid`) und `review_required` umgesetzt
- Kennzeichen-Normalisierung und Plausibilitäts-/Pflichtfeldprüfung umgesetzt
- E-Mail-Übergabe an das Büro implementiert: HTML- und Textformat, explizite Mechaniker-Bestätigung sowie SMTP-Konfiguration über Umgebungsvariablen
- Persistente SQLite-Outbox für Versandstatus, fehlgeschlagene Zustellungen, Neustartsicherheit und erneutes Senden umgesetzt
- Frontend als React-/TypeScript-PWA umgesetzt: Start-, Übersichts-, Erfassungs-, Korrektur-, Bestätigungs- und Fehleransichten für Reifenwechsel und Reifeneinlagerung
- Frontend und Backend über den gemeinsamen `RegistrationDraft`-Vertrag integriert; Backend-Validierung, Versandstatus und Wiederholungsversand werden in der Mechanikeransicht angezeigt
- Anonymisierte End-to-End-Testfälle für typische Werkstattformulierungen als Regressionsvertrag abgedeckt

## In Arbeit

- Review 1 des manuellen Kernablaufs: Reifenwechsel und Reifeneinlagerung müssen gemeinsam mit der Werkstatt vollständig durchgespielt und fachlich abgenommen werden
- Verbindliche Abstimmung des Datenmodells mit der Werkstatt: Pflichtfelder, bedingte Angaben, Statusmodell und Verantwortlichkeiten
- Vorbereitung der realen Betriebsumgebung: SMTP-Zugang, Empfängeradresse und dauerhaftes, zugriffsgeschütztes Speicherziel für die Outbox konfigurieren und testen

## Als Nächstes

1. Manuellen Ablauf für beide Vorgangstypen inklusive Korrekturen, Validierungsfehlern, Bestätigung und E-Mail-Übergabe im Werkstattkontext testen.
2. Offene fachliche Punkte priorisieren und die bestätigten Regeln in Datenmodell, Validierung, Oberfläche und Tests übernehmen.
3. Audioaufnahme im Browser, Audio-Upload sowie Speech-to-Text anbinden und auf Smartphone/Tablet prüfen.
4. KI-Extraktion nach den vorhandenen Extraktionsregeln integrieren; Unsicherheiten weiterhin markieren statt Werte zu erraten.
5. Strukturierte E-Mail-Ausgabe mit dem Büro anhand realitätsnaher, anonymisierter Vorgänge abnehmen und die Retry-Strecke testen.

## Aktuell offene Fragen und Abgrenzungen

- Die fachlichen Formularangaben bilden den implementierten vorläufigen Vertrag, sind aber noch nicht durch die Werkstatt verbindlich bestätigt oder rechtlich geprüft.
- Es ist zu klären, welche Felder je Vorgangstyp zwingend, optional oder nur bei bestimmten Befunden erforderlich sind und wer spätere Regeländerungen verantwortet.
- Speech-to-Text, KI-Extraktion und die Verarbeitung echter Audiodaten sind noch nicht implementiert; die vorhandenen Testfälle testen den Übergabevertrag, nicht externe KI- oder Sprachdienste.
- Eine produktive SMTP-Zustellung wurde noch nicht mit den realen Zugangsdaten und dem Büroempfänger verifiziert.
- Die vorläufige Mechaniker-ID muss vor Produktivbetrieb durch eine authentifizierte Identität ersetzt werden.
- WERBAS bleibt im MVP führendes System. Eine direkte WERBAS-Anbindung, zentrale Büro-Inbox und zentrale Fachspeicherung gehören weiterhin nicht zum MVP.

## Wichtiger Hinweis

Die aktuelle Implementierung bildet die verfügbaren Formularangaben technisch ab. Sie ersetzt keine bestätigten Werkstatt-, Hersteller- oder Rechtsvorgaben. Erst nach der fachlichen Abstimmung dürfen daraus verbindliche Pflichtfeldprüfungen und Arbeitsanweisungen abgeleitet werden.
