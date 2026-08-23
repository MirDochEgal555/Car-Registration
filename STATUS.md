# Projektstatus

## Fertig
- MVP-Scope und grundlegender Ablauf definiert
- Zeitplan bis zum Werkstatttest erstellt
- Tech-Stack festgelegt
- Backend-MVP mit Validierungs-API, E-Mail-Versand und persistenter Versand-Outbox umgesetzt und getestet
- Deutsche Backend-Dokumentation mit Architektur- und Kohärenzbewertung erstellt

## In Arbeit
- Fachliches Datenmodell für Fahrzeug-, Reifen- und Vorgangsdaten mit der Werkstatt abstimmen
- Pflichtfelder, Statusmodell und Verantwortlichkeiten verbindlich konkretisieren
- Formularangaben den tatsächlichen Werkstatt-, Hersteller- und gegebenenfalls rechtlichen Vorgaben zuordnen

## Als Nächstes
- Frontend für die Mechaniker-Erfassung auf Basis der vorhandenen Formularangaben und des bestehenden API-Vertrags aufsetzen
- Benutzerabläufe für Mechaniker und Büro finalisieren
- Regeln für Spracheingabe und strukturierte Extraktion definieren
- Repräsentative Testfälle für typische Werkstattformulierungen erstellen
- Bestätigungsansicht für Mechaniker und Prüfungsansicht für das Büro umsetzen
- Anschließend Rücksprache mit der Werkstatt zu den vorhandenen Formularen durchführen: Welche Angaben sind zwingend, optional oder nur bei einem bestimmten Befund erforderlich?
- Gesetzliche, Hersteller- und betriebliche Vorgaben für Reifenwechsel und Reifeneinlagerung klären
- Die bestätigten Vorgaben als fachliche Regeln, Pflichtfeldprüfungen und Frontend-Hinweise in Backend und Oberfläche übernehmen
- Testbetrieb in der Werkstatt vorbereiten und durchführen

## Aktuell offene Fragen
- Die Angaben der vorhandenen Reifenformulare liegen als vorläufige Grundlage vor. Sie sind jedoch noch nicht durch Rücksprache mit der Werkstatt als verbindlich bestätigt.
- Welche Felder sind je Vorgangstyp zwingend, welche optional und welche nur bei bestimmten Befunden erforderlich?
- Welche Angaben müssen aufgrund gesetzlicher, Hersteller- oder interner Werkstattvorgaben erfasst, geprüft oder aufbewahrt werden?
- Wer bestätigt die fachlichen Regeln und hält spätere Änderungen der Formulare oder Vorschriften nach?

## Wichtiger Hinweis zum Backend

Die aktuellen Backend-Modelle und Validierungsregeln bilden die verfügbaren Formularangaben ab. Das als Nächstes geplante Frontend verwendet diese Angaben bewusst als vorläufigen Vertrag. Erst danach werden die Regeln mit der Werkstatt abgestimmt, dokumentiert und als verbindliche Vorgaben im Backend, im Frontend und in den Tests umgesetzt. Sie stellen bis dahin keine bestätigte oder rechtlich geprüfte Umsetzung von Werkstattvorschriften dar.
