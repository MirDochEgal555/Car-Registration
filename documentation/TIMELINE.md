# Fahrzeug- & Reifenerfassung – Zeitplan

## Ziel

Bis spätestens **15.10.2026** muss das MVP im Werkstattalltag zuverlässig funktionieren.

Das bedeutet:

- Mechaniker erfassen Fahrzeug- und Reifendaten primär per Sprache.
- Strukturierte Daten werden korrekt extrahiert.
- Unsichere Angaben werden markiert und nicht geraten.
- Mechaniker bestätigen Vorgänge mit minimaler Interaktion.
- Das Büro prüft und korrigiert offene Vorgänge.
- Daten werden zuverlässig gespeichert.
- Jeder abgesendete Vorgang erscheint in der Büro-Inbox und löst eine E-Mail-Benachrichtigung aus.
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
→ Daten prüfen
→ Vorgang finalisieren
```

#### Ergebnis

Ein stabiler fachlicher Scope bildet die Grundlage der Implementierung.

## Phase 2 – Backend und Datenmodell

### 23.08.–29.08.

Ziel: Das technische Fundament bereitstellen.

#### Aufgaben

- FastAPI-Projekt aufsetzen
- PostgreSQL anbinden
- SQLAlchemy-Modelle erstellen
- Migrationen einrichten
- zentrale API-Struktur definieren
- Modelle für `Vehicle`, `ServiceRecord`, `TireSet`, `ServiceTireSet`, `TireInspection` und `TireCondition` implementieren
- Statuslogik implementieren
- Feldstatus für `missing`, `uncertain` und `invalid` sowie `review_required` implementieren
- KI-Rohdaten und Audit-Informationen speichern
- zentrale Speicherung beim Absenden und Benachrichtigungsauftrag atomar anlegen

Bestätigungen und Korrekturen werden als Herkunfts- und Audit-Informationen gespeichert, nicht als zusätzliche Feldstatus.

#### Ergebnis

Fahrzeug- und Reifeninformationen können vollständig strukturiert gespeichert und über die API gelesen und geschrieben werden.

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

## Phase 4 – Büroprüfung (Basis)

### 06.09.–12.09.

Ziel: Das Büro kann direkt nach Fertigstellung des Mechaniker-Frontends erste Vorgänge prüfen und korrigieren.

#### Aufgaben

- Liste offener Vorgänge
- Inbox-Status Neu, Prüfen und Erledigt
- Detailansicht für manuell erfasste Vorgänge
- Felder bearbeiten
- Kunden neu anlegen oder zuordnen
- Vorgang abschließen
- Korrekturen nachvollziehbar speichern
- kurze E-Mail-Benachrichtigung nach jedem abgesendeten Vorgang testen

#### Ergebnis

Der durchgängige Ablauf von Mechaniker-Frontend zu Büroprüfung ist bereits ohne Spracheingabe testbar. Diese Phase läuft parallel zur Speech-to-Text-Anbindung.

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

## Phase 7 – Integrierte Büroprüfung

### 19.09.–24.09.

Ziel: Das Büro kann KI- und Mechanikerdaten effizient prüfen.

#### Aufgaben

- Liste offener Vorgänge
- Statuswechsel Neu → Prüfen → Erledigt
- Detailansicht
- Unsicherheiten hervorheben
- Originaltranskript anzeigen
- ursprüngliche KI-Ausgabe anzeigen
- Mechanikerkorrekturen nachvollziehbar machen
- Felder bearbeiten
- Kunden neu anlegen oder zuordnen
- Vorgang abschließen
- E-Mail-Inhalt mit Kennzeichen, Absendezeitpunkt und authentifiziertem Link prüfen

#### Ergebnis

Der vollständige Ablauf funktioniert:

```text
Mechaniker
→ KI-Extraktion
→ Bestätigung
→ Büroprüfung
→ Finalisierung
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
- Datenbankfehler testen
- langsame Netzwerkverbindungen testen
- Smartphone- und Tablet-Tests
- Desktop-Tests für das Büro
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
- Büroprüfung und Kundenzuordnung
- Finalisierung
- Datenbankpersistenz
- Neustart des Systems
- Backup
- Smartphone, Tablet und Büro-PC

#### Go-Live-Kriterium

Kein Fehler darf einen normalen Werkstattvorgang blockieren.

## Produktiver Start

### 15.10.2026

Das System ist für den realen Werkstattbetrieb freigegeben. Eine WERBAS-Integration gehört nicht zum MVP; die Datenstruktur bleibt dafür vorbereitet.

## Meilensteine

| Datum | Meilenstein |
| --- | --- |
| 22.08. | Spezifikation abgeschlossen |
| 29.08. | Backend und Datenmodell stehen |
| 05.09. | Mechaniker-Frontend funktioniert |
| 12.09. | erste Büroprüfung und Speech-to-Text funktionieren |
| 18.09. | KI-Extraktion funktioniert |
| 24.09. | integrierte Büroprüfung funktioniert |
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
11. Büroprüfung
12. persistente Speicherung

### Kann reduziert werden

- aufwendiges UI-Design
- erweiterte Analysen
- umfangreiche Rollenverwaltung
- detailliertes Audit-Frontend
- bestehende Kundenerkennung
- Automatisierungen
- zusätzliche Servicearten

### Nicht vor dem 15.10. erforderlich

- direkte WERBAS-API
- manuelle oder automatische WERBAS-Übergabe als Teil des MVP-Ablaufs
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
- das Büro offene Vorgänge vollständig prüfen kann,
- jeder abgesendete Vorgang zentral gespeichert, in der Inbox sichtbar und per E-Mail angekündigt wird,
- Kunden ausschließlich im Büro angelegt oder zugeordnet werden,
- Daten auch nach einem Neustart vorhanden sind,
- typische reale Werkstattformulierungen funktionieren und
- der Pilot keine kritischen Blocker mehr zeigt.
