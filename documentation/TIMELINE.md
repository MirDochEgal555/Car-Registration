# Fahrzeug- & Reifenerfassung – Zeitplan

## Ziel

Bis spätestens **15.10.2026** muss das MVP im Werkstattalltag zuverlässig funktionieren.

Das bedeutet:

- Mechaniker erfassen Fahrzeug- und Reifendaten primär per Sprache.
- Strukturierte Daten werden korrekt extrahiert.
- Unsichere Angaben werden markiert und nicht geraten.
- Mechaniker bestätigen Vorgänge mit minimaler Interaktion.
- Das Büro erhält strukturierte Protokolle per E-Mail, prüft sie und speichert sie in WERBAS.
- Jeder abgesendete Vorgang löst eine strukturierte E-Mail aus.
- Typische Werkstattformulierungen funktionieren robust.
- Kritische Fehler sind behoben.
- Das System ist für den täglichen Einsatz stabil genug.

> Der 15.10.2026 ist nicht der Entwicklungsschluss, sondern der Termin, ab dem das System zuverlässig produktiv nutzbar sein soll.

## Phase 1 – Spezifikation finalisieren

### 19.08.–22.08.

Ziel: Vor der Implementierung alle zentralen Entscheidungen festlegen.

#### Aufgaben

- [Projektübersicht](PROJECT.md) finalisieren
- [Tech-Stack](TECH_STACK.md) finalisieren
- [Datenmodell](DATA_MODEL.md) finalisieren
- [Benutzerablauf](USER_FLOW.md) finalisieren
- [Extraktionsregeln](EXTRACTION_RULES.md) finalisieren
- [Extraktions-Testfälle](TEST_CASES.md) finalisieren
- Pflichtfelder definieren
- Statusmodell definieren
- Verantwortlichkeiten von Mechaniker und Büro eindeutig festlegen

#### Wichtige Entscheidung

Der Mechaniker legt keinen Kunden an.

```text
Mechaniker
→ Kennzeichen und Serviceinformationen erfassen
→ Reifendaten erfassen
→ bestätigen

Büro
→ Kunden neu anlegen oder zuordnen
→ strukturierte E-Mail prüfen
→ Vorgang in WERBAS speichern und finalisieren
```

#### Ergebnis

Ein stabiler fachlicher Scope bildet die Grundlage der Implementierung.

## Phase 2 – Backend und Datenmodell

### 23.08.–29.08.

Ziel: Das technische Fundament bereitstellen.

#### Aufgaben

- FastAPI-Projekt aufsetzen
- zentrale API-Struktur definieren
- Feldstatus für `missing`, `uncertain` und `invalid` sowie `review_required` implementieren
- strukturiertes E-Mail-Format aus dem Entwurf erzeugen
- SMTP- oder E-Mail-Dienst anbinden
- Versandfehler und erneutes Absenden behandeln

Das [Datenmodell](DATA_MODEL.md) bleibt als Struktur für E-Mail-Ausgabe und eine mögliche spätere zentrale Speicherung erhalten.

#### Ergebnis

Fahrzeug- und Reifeninformationen können vollständig strukturiert aufbereitet und als E-Mail an das Büro versendet werden.

## Phase 3 – Mechaniker-Frontend

### 30.08.–05.09.

Ziel: Der Kernworkflow funktioniert zunächst ohne KI vollständig.

#### Aufgaben

- React, TypeScript und Vite aufsetzen
- PWA konfigurieren
- Mechanikeransicht erstellen
- Reifenwechsel- oder Einlagerungsprotokoll auswählen und starten
- Kennzeichen und Reifendaten erfassen und anzeigen
- Daten korrigieren
- Vorgang bestätigen
- Fehlerzustände anzeigen
- große, werkstatttaugliche Bedienelemente umsetzen

#### Zielablauf

```text
Neue Erfassung
→ Daten vorhanden
→ Mechaniker prüft
→ bestätigt
```

#### Ergebnis

Der vollständige Ablauf kann bereits manuell getestet werden.

## Phase 4 – Strukturierte E-Mail-Ausgabe

### 06.09.–12.09.

Ziel: Das Büro erhält nach jeder Mechanikerbestätigung ein vollständig strukturiertes Protokoll zur Übernahme in WERBAS.

#### Aufgaben

- E-Mail-Template für Reifenwechsel und Reifeneinlagerung erstellen
- Kennzeichen, Zeitpunkt und alle strukturierten Werte ausgeben
- fehlende, unsichere und unplausible Felder als Prüfhinweise ausgeben
- E-Mail-Versand nach der Mechanikerbestätigung testen
- Versandfehler anzeigen und erneutes Absenden ermöglichen
- manuelle Übernahme in WERBAS mit dem Büro testen

#### Ergebnis

Der durchgängige Ablauf von Mechaniker-Frontend über E-Mail bis zur Übernahme in WERBAS ist bereits ohne Spracheingabe testbar. Diese Phase läuft parallel zur Speech-to-Text-Anbindung.

## Phase 5 – Speech-to-Text

### 06.09.–12.09.

Ziel: Der Mechaniker kann statt manueller Eingabe natürlich sprechen.

#### Aufgaben

- Audioaufnahme im Browser
- `MediaRecorder`-API
- Audio-Upload
- Speech-to-Text anbinden
- deutsches Werkstattvokabular testen
- Zahlen und Kennzeichen testen
- Fehlerbehandlung umsetzen
- Transkript speichern und anzeigen

#### Testschwerpunkte

- Kennzeichen
- Kilometerstände
- Reifengrößen
- Hersteller
- Modellnamen
- Profiltiefen
- Vorder- und Hinterachse
- links und rechts

#### Ergebnis

Gesprochene Werkstattsprache wird zuverlässig als Text erfasst.

## Phase 6 – KI-Extraktion und Validierung

### 13.09.–18.09.

Ziel: Sprache wird automatisch in das interne Datenmodell übersetzt.

#### Aufgaben

- Schema für strukturierte Ausgaben definieren
- Extraktionsprompt implementieren
- Kennzeichen normalisieren
- Kilometerstand extrahieren
- Reifenart extrahieren
- Reifengröße normalisieren
- Hersteller und Modell unterscheiden
- Anzahl extrahieren
- Profiltiefen und Reifenpositionen erkennen
- Reifenzustände extrahieren
- Servicehinweise erkennen
- Korrekturen innerhalb einer Aussage berücksichtigen
- Unsicherheiten markieren
- Plausibilitätsprüfungen implementieren

#### Kritische Regel

```text
Unbekannt ≠ plausibel ergänzen
```

Bei Unsicherheit:

```json
{
  "model": null,
  "field_status": {
    "model": "uncertain"
  },
  "review_required": true
}
```

#### Ergebnis

Die dokumentierten [Extraktions-Testfälle](TEST_CASES.md) laufen weitgehend automatisiert durch.

## Phase 7 – E-Mail-Übergabe validieren

### 19.09.–24.09.

Ziel: Die E-Mail-Ausgabe ist für die verlässliche manuelle Übernahme in WERBAS vollständig und verständlich.

#### Aufgaben

- E-Mail-Inhalt für beide Protokolltypen prüfen
- Unsicherheiten, fehlende und unplausible Werte als Prüfhinweise hervorheben
- Originaltranskript und KI-Ausgabe bei Bedarf in die E-Mail aufnehmen
- Mechanikerkorrekturen in der E-Mail nachvollziehbar ausgeben
- Übernahme der Daten in WERBAS mit Büroanwendern testen
- E-Mail-Inhalt mit Kennzeichen und Absendezeitpunkt prüfen

#### Ergebnis

Der vollständige Ablauf funktioniert:

```text
Mechaniker
→ KI-Extraktion
→ Bestätigung
→ strukturierte E-Mail
→ Übernahme und Finalisierung in WERBAS
```

## Phase 8 – Interner Integrationstest

### 25.09.–30.09.

Ziel: Alle Komponenten gemeinsam testen.

#### Aufgaben

- vollständige End-to-End-Tests
- Fehlerfälle provozieren
- ungültige Eingaben testen
- schlechte Spracheingaben testen
- doppelte Vorgänge testen
- E-Mail-Versandfehler und erneutes Absenden testen
- langsame Netzwerkverbindungen testen
- Smartphone- und Tablet-Tests
- E-Mail-Darstellung am Büro-Arbeitsplatz testen
- Browser-Kompatibilität prüfen

#### Testdatensatz

Mindestens 30–50 realistische Werkstattformulierungen testen. Berücksichtigt werden auch:

- Dialekt
- Versprecher
- Selbstkorrekturen
- unvollständige Aussagen
- abweichende Reihenfolgen
- Hintergrundgeräusche
- Abkürzungen

#### Ergebnis

Im normalen Ablauf bestehen keine bekannten Blocker.

## Phase 9 – Werkstatt-Pilot

### 01.10.–05.10.

Ziel: Reale Nutzung mit echten Mechanikern testen.

#### Pilotumfang

Idealerweise werden 10–20 echte Vorgänge erfasst. Der bestehende manuelle Prozess bleibt parallel als Fallback erhalten.

#### Messen

- Zeit pro Erfassung
- Anzahl notwendiger Klicks
- Anzahl notwendiger Korrekturen
- Speech-to-Text-Fehler
- Extraktionsfehler
- fehlende Felder
- Aufwand der Büroprüfung
- subjektive Belastung der Mechaniker

#### Beobachten

- Wo spricht der Mechaniker anders als erwartet?
- Welche Felder werden häufig vergessen?
- Welche UI-Elemente stören?
- Welche Informationen werden in der Praxis anders beschrieben?
- Welche Angaben sind für das Büro tatsächlich wichtig?

#### Ergebnis

Reale Schwachstellen sind bekannt und priorisiert.

## Phase 10 – Stabilisierung

### 06.10.–10.10.

Ziel: Keine neuen Features mehr hinzufügen.

#### Fokus

- Fehler
- Extraktionsfehler
- schlechte Benutzerführung
- fehlende Validierung
- Performance
- Stabilität
- Datenkonsistenz

#### Feature Freeze

Ab **06.10.2026** werden keine neuen Features mehr umgesetzt. Ausnahme: Ein fehlendes Feature verhindert einen Kernprozess.

#### Ergebnis

Ein Release Candidate liegt vor.

## Phase 11 – Go-Live-Prüfung und Puffer

### 11.10.–14.10.

Ziel: Den vollständigen Ablauf vor dem produktiven Start testen und verbleibende kritische Fehler beheben.

#### Prüfen

- neue Fahrzeugerfassung
- Reifenwechsel
- Reifeneinlagerung
- vollständige und unvollständige Spracheingaben
- Korrekturen durch den Mechaniker
- E-Mail-Ausgabe und manuelle Übernahme in WERBAS
- Kundenzuordnung und Finalisierung in WERBAS
- erneutes Absenden nach einem E-Mail-Fehler
- Smartphone, Tablet und Büro-PC

#### Go-Live-Kriterium

Kein Fehler darf einen normalen Werkstattvorgang blockieren.

## Produktiver Start

### 15.10.2026

Das System ist für den realen Werkstattbetrieb freigegeben. WERBAS bleibt das führende Speichersystem; der MVP übergibt die strukturierten Protokolle per E-Mail und nutzt keine direkte technische Integration.

## Meilensteine

| Datum | Meilenstein |
| --- | --- |
| 22.08. | Spezifikation abgeschlossen |
| 29.08. | Backend und Datenmodell stehen |
| 05.09. | Mechaniker-Frontend funktioniert |
| 12.09. | strukturierte E-Mail-Ausgabe und Speech-to-Text funktionieren |
| 18.09. | KI-Extraktion funktioniert |
| 24.09. | E-Mail-Übergabe an WERBAS validiert |
| 30.09. | Integrationstest abgeschlossen |
| 05.10. | Werkstatt-Pilot abgeschlossen |
| 06.10. | Feature Freeze |
| 10.10. | Stabilisierung abgeschlossen |
| 14.10. | finaler Go-Live-Test |
| **15.10.** | **produktiver Einsatz** |

## Prioritäten bei Zeitproblemen

### Muss funktionieren

1. Spracheingabe
2. Kennzeichen
3. Kilometerstand
4. Reifenart
5. Reifengröße
6. Hersteller und Modell
7. Anzahl
8. Profiltiefe
9. Reifenzustand
10. Mechanikerbestätigung
11. strukturierte E-Mail-Ausgabe
12. erfolgreicher E-Mail-Versand mit Wiederholen bei Fehlern

### Kann reduziert werden

- aufwendiges UI-Design
- erweiterte Analysen
- umfangreiche Rollenverwaltung
- detailliertes Audit-Frontend
- bestehende Kundenerkennung
- zentrale Speicherung und Büro-Inbox
- Automatisierungen
- zusätzliche Servicearten

### Nicht vor dem 15.10. erforderlich

- direkte WERBAS-API
- zentrale Speicherung in der CarTech-Anwendung
- Büro-Inbox oder Büro-Bearbeitung in der CarTech-Web-App
- Schadensfotos
- native App
- komplexe Kundenerkennung
- Microservices
- weitere Werkstattprozesse

## Abnahmekriterien

Der MVP ist fertig, wenn:

- ein Mechaniker einen Reifenwechsel oder eine Reifeneinlagerung primär per Sprache dokumentieren kann,
- im Standardfall nur minimale Interaktion nötig ist,
- keine unsicheren Informationen erfunden werden,
- relevante Reifeninformationen korrekt strukturiert werden,
- falsche Werte schnell korrigierbar sind,
- das Büro die strukturierten E-Mails vollständig in WERBAS übernehmen und dort prüfen kann,
- jeder abgesendete Vorgang eine vollständige strukturierte E-Mail mit Prüfhinweisen erzeugt,
- Kunden ausschließlich im Büro angelegt oder zugeordnet werden,
- typische reale Werkstattformulierungen funktionieren und
- der Pilot keine kritischen Blocker mehr zeigt.
