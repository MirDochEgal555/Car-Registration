# Benutzerablauf

## Ziel

Der Mechaniker soll möglichst wenig tippen oder klicken.

```text
Mechaniker spricht
→ KI extrahiert
→ Mechaniker bestätigt
→ Büro prüft
→ Datensatz abgeschlossen
```

## Hauptrollen

### Mechaniker

Aufgaben:

- neue Fahrzeug- oder Serviceerfassung starten
- Informationen einsprechen
- KI-Ergebnis kurz kontrollieren
- fehlerhafte oder fehlende Daten korrigieren
- Datensatz bestätigen

Der Mechaniker erstellt oder ordnet keine Kunden zu.

### Büro

Aufgaben:

- offene Vorgänge prüfen
- erkannte Daten korrigieren
- fehlende Kundendaten ergänzen
- Kunden zuordnen oder neu anlegen
- Vorgang finalisieren
- Daten im MVP manuell nach WERBAS übernehmen

## Statusablauf

```text
Neue Erfassung: draft
Nach Extraktion: mechanic_review
Nach Mechanikerbestätigung: office_review
Nach Büroprüfung: completed
Bei Abbruch: rejected
```

Unsicherheiten und Plausibilitätsfehler ändern den Ablaufstatus nicht. Sie werden separat durch Feldstatus und `review_required` gekennzeichnet.

## Flow 1: Neue Erfassung

### Schritt 1 – Vorgang starten

Der Mechaniker öffnet die neue Fahrzeugaufnahme. Die App zeigt möglichst nur eine primäre Aktion:

```text
Aufnahme starten
```

Dadurch entsteht ein Vorgang mit dem Status `draft`.

### Schritt 2 – Spracheingabe

Beispiel:

> „CW AB 123, 73.400 Kilometer, vier Michelin Alpin 6 Winterreifen, 205 55 16, vorne sechs Millimeter, hinten fünf.“

Der Mechaniker muss keine feste Reihenfolge einhalten. Er startet die Fahrzeug- oder Serviceerfassung über das Kennzeichen; ein Kundenobjekt wird dabei nicht angelegt.

### Schritt 3 – Verarbeitung

Das System:

1. nimmt Audio auf,
2. führt Speech-to-Text durch,
3. extrahiert einen strukturierten Entwurf,
4. validiert die Daten und
5. markiert Unsicherheiten.

Währenddessen zeigt die App:

```text
Daten werden verarbeitet …
```

Nach erfolgreicher Extraktion erhält der Vorgang den Status `mechanic_review`.

### Schritt 4 – Mechanikerprüfung

Die wichtigsten Werte werden kompakt angezeigt:

```text
CW-AB 123
73.400 km

Winterreifen
Michelin Alpin 6
205/55 R16
4 Stück

Profil
Vorne 6 mm
Hinten 5 mm
```

Unsichere Informationen werden deutlich markiert:

```text
Reifenmodell: Alpin 6 [unsicher]
```

### Schritt 5 – Fehlende Informationen

Fehlende Pflichtinformationen werden hervorgehoben:

```text
Kennzeichen fehlt
```

Das System soll eine kurze ergänzende Spracheingabe erlauben:

> „Kennzeichen CW AB 123.“

Danach wird nur das betroffene Feld aktualisiert.

### Schritt 6 – Mechanikerbestätigung

Die primäre Aktion lautet:

```text
Bestätigen
```

Nach der Bestätigung erhält der Vorgang den Status `office_review`. Der Mechaniker ist fertig.

## Flow 2: Büroprüfung

Das Büro öffnet die Liste offener Vorgänge, zum Beispiel:

```text
CW-AB 123
19.08.2026
Reifenwechsel
Mechaniker bestätigt
```

In der Detailansicht sind verfügbar:

- geprüfte Mechanikerdaten
- markierte Unsicherheiten und Plausibilitätsfehler
- Originaltranskript
- ursprüngliche KI-Extraktion
- Korrekturen des Mechanikers

Das Büro kann jedes relevante Feld bearbeiten, den Kunden zuordnen oder neu anlegen und zusätzliche Kundendaten ergänzen.

Nach der Prüfung wählt das Büro:

```text
Vorgang abschließen
```

Der Status wird `completed`. Anschließend können die Daten manuell nach WERBAS übernommen werden.

## Flow 3: Fehlerhafte Erkennung

Gesprochen:

> „Continental WinterContact“

Fehlerhaft erkannt:

```text
Continental Winter Count
```

Der Mechaniker kann das Feld antippen und korrigieren oder per Sprache berichtigen:

> „Reifenmodell WinterContact.“

Das System aktualisiert nur das betreffende Feld.

## Flow 4: Unsichere oder nicht verstandene Sprache

Bei unsicheren Angaben darf keine automatische Ergänzung erfolgen. Das Feld wird als unsicher markiert und der Vorgang erhält `review_required: true`; der Mechaniker kann fortfahren, wenn das Feld nicht erforderlich ist.

Wenn Speech-to-Text nicht zuverlässig gelingt, zeigt die App:

```text
Spracheingabe konnte nicht zuverlässig erkannt werden.
```

Mögliche Aktionen:

- erneut aufnehmen
- Transkript anzeigen und bearbeiten

Es werden keine geratenen Daten übernommen.

## Flow 5: Saisonaler Reifenwechsel

Beispiel:

> „Wechsel auf Winterreifen. Eingelagert werden vier Michelin Sommerreifen 225 45 17.“

Das System legt mehrere Reifensätze mit klarer Rolle an:

```text
installed: Winterreifen
stored: Michelin Sommerreifen, 225/45 R17, vier Stück
```

Die erwähnten Sommerreifen dürfen nicht als montierter Satz gespeichert werden.

## UI-Prinzipien

### Mechanikeransicht

Priorität:

```text
Sprechen > Tippen
```

- große Buttons
- wenige Felder gleichzeitig
- keine langen Formulare
- möglichst keine Dropdown-Ketten
- wichtigste Aktion immer sichtbar
- Fehler direkt und verständlich anzeigen

### Büroansicht

Priorität:

```text
Kontrolle > Geschwindigkeit
```

- vollständige Übersicht
- schnelle Korrekturen
- sichtbare Unsicherheiten
- verfügbares Originaltranskript

## Zielwerte für den MVP

Ein normaler Vorgang soll idealerweise nur diese Mechanikerinteraktionen benötigen:

```text
1× Aufnahme starten
1× sprechen
1× bestätigen
```

Zusätzliche Interaktion ist nur bei fehlenden oder falsch erkannten Daten vorgesehen.
