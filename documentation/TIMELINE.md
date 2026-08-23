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

> **Planungsprinzip:** Entwicklungsblöcke sind auf höchstens vier Kalendertage begrenzt. Nach jedem wesentlichen Baustein ist eine eigene Review- und Abnahmephase eingeplant; erkannte kritische Abweichungen werden dort vor dem nächsten Entwicklungsblock geschlossen.

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

## Phase 2 – Backend und Datenmodell entwickeln

### 23.08.–26.08.

Ziel: Das technische Fundament in einem klar begrenzten Entwicklungsblock bereitstellen.

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

## Phase 3 – Mechaniker-Frontend entwickeln

### 27.08.–30.08.

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

## Phase 4 – Review 1: manueller Kernablauf

### 31.08.–03.09.

Ziel: Backend, Datenmodell und Mechaniker-Frontend gemeinsam prüfen, bevor weitere Funktionen darauf aufbauen.

#### Reviewumfang

- manuelle Erfassung eines Reifenwechsels und einer Einlagerung vollständig durchspielen
- Pflichtfelder, Feldstatus und `review_required` gegen Datenmodell und Fachlichkeit prüfen
- Eingabekorrekturen, Fehlerzustände und Bestätigung aus Sicht der Mechaniker prüfen
- API-Verträge und Datenübergabe zwischen Frontend und Backend prüfen
- offene Punkte priorisieren und kritische Abweichungen innerhalb der Review-Phase beheben

#### Abnahmekriterium

Der manuelle Kernablauf funktioniert für beide Vorgangstypen ohne Blocker. Erst dann beginnt die Anbindung von Sprache und E-Mail.

## Phase 5 – Strukturierte E-Mail-Ausgabe und Speech-to-Text entwickeln

### 04.09.–07.09.

Ziel: E-Mail-Übergabe und Spracheingabe in einem kurzen, parallelen Entwicklungsblock umsetzen.

#### Aufgaben

- E-Mail-Template für Reifenwechsel und Reifeneinlagerung erstellen
- Kennzeichen, Zeitpunkt und alle strukturierten Werte ausgeben
- fehlende, unsichere und unplausible Felder als Prüfhinweise ausgeben
- E-Mail-Versand nach der Mechanikerbestätigung testen
- Versandfehler anzeigen und erneutes Absenden ermöglichen
- Audioaufnahme im Browser und `MediaRecorder`-API umsetzen
- Audio-Upload und Speech-to-Text anbinden
- deutsches Werkstattvokabular, Zahlen und Kennzeichen testen
- Fehlerbehandlung umsetzen sowie Transkript speichern und anzeigen

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

E-Mail-Übergabe und gesprochene Werkstattsprache stehen für die gemeinsame Review bereit.

## Phase 6 – Review 2: Übergabe und Spracheingabe

### 08.09.–11.09.

Ziel: Den Ablauf vom gesprochenen Wort bis zur nachvollziehbaren E-Mail prüfen und fachlich abnehmen.

#### Reviewumfang

- Sprachaufnahme, Upload, Transkript und Fehlerbehandlung auf Smartphone und Tablet prüfen
- Kennzeichen, Zahlen und Werkstattvokabular anhand repräsentativer Beispiele bewerten
- E-Mail-Templates für beide Protokolltypen mit dem Büro auf Verständlichkeit und Vollständigkeit prüfen
- Versandfehler, erneutes Absenden und Anzeige für Mechaniker durchspielen
- Befunde dokumentieren, priorisieren und kritische Punkte vor dem nächsten Entwicklungsblock schließen

#### Abnahmekriterium

Die manuelle und sprachbasierte Erfassung liefern einen nachvollziehbaren Vorgang; das Büro kann die E-Mail ohne Informationsverlust prüfen.

## Phase 7 – KI-Extraktion und Validierung entwickeln

### 12.09.–15.09.

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

Die dokumentierten [Extraktions-Testfälle](TEST_CASES.md) stehen zur fachlichen Abnahme bereit.

## Phase 8 – Review 3: Extraktionsqualität und Validierung

### 16.09.–20.09.

Ziel: Die KI-Ausgabe fachlich absichern, bevor sie in den Werkstattprozess übernommen wird.

#### Reviewumfang

- alle dokumentierten Extraktions-Testfälle automatisiert ausführen und Fehlklassifikationen bewerten
- mindestens 30 realistische Werkstattformulierungen einschließlich Dialekt, Versprecher und Selbstkorrekturen manuell prüfen
- Unsicherheiten, fehlende und unplausible Werte gezielt auf korrektes Markieren statt Raten prüfen
- Mechanikerkorrekturen gegen Transkript, KI-Ausgabe und Datenmodell nachvollziehen
- kritische und häufige Fehler priorisieren sowie Korrekturen validieren

#### Abnahmekriterium

Keine unsichere Information wird als sicher ausgegeben. Die Muss-Felder aus den Testfällen sind entweder korrekt extrahiert oder eindeutig als fehlend beziehungsweise unsicher markiert.

## Phase 9 – Review 4: E-Mail-Übergabe an WERBAS

### 21.09.–24.09.

Ziel: Die E-Mail-Ausgabe mit Büroanwendern für die verlässliche manuelle Übernahme in WERBAS abnehmen.

#### Reviewumfang

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

## Phase 10 – Interner Integrations- und Abnahmetest

### 25.09.–30.09.

Ziel: Alle abgenommenen Komponenten gemeinsam unter realitätsnahen Bedingungen testen.

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

## Phase 11 – Werkstatt-Pilot

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

## Phase 12 – Stabilisierung und Review

### 06.10.–10.10.

Ziel: Keine neuen Features mehr hinzufügen, Korrekturen umsetzen und den Release Candidate erneut prüfen.

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

#### Reviewabschluss

- alle Korrekturen aus dem Werkstatt-Pilot per Regressionstest prüfen
- kritische Kernabläufe auf Smartphone, Tablet und Büro-PC erneut durchspielen
- nur Fehler mit Go-Live-Relevanz in den Release Candidate übernehmen

#### Ergebnis

Ein geprüfter Release Candidate liegt vor.

## Phase 13 – Go-Live-Review und Puffer

### 11.10.–14.10.

Ziel: Den vollständigen Ablauf vor dem produktiven Start formell freigeben und verbleibende kritische Fehler beheben.

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
| 26.08. | Backend und Datenmodell entwickelt |
| 30.08. | Mechaniker-Frontend entwickelt |
| 03.09. | manueller Kernablauf abgenommen |
| 07.09. | strukturierte E-Mail-Ausgabe und Speech-to-Text entwickelt |
| 11.09. | Übergabe und Spracheingabe abgenommen |
| 15.09. | KI-Extraktion entwickelt |
| 20.09. | Extraktionsqualität und Validierung abgenommen |
| 24.09. | E-Mail-Übergabe an WERBAS abgenommen |
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
