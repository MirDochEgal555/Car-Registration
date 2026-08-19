# CarTech – Projektübersicht

## Ziel

CarTech vereinfacht die Fahrzeugaufnahme und saisonale Reifenwechsel in kleinen Werkstätten. Mechaniker erfassen Informationen per Sprache; das Büro prüft und vervollständigt den Datensatz, bevor die Daten im MVP manuell nach WERBAS übernommen werden.

Der MVP umfasst zwei Vorgangstypen:

- Neukundenaufnahme
- saisonaler Reifenwechsel

## Ausgangslage

Der bisherige Ablauf ist papierbasiert:

```text
Mechaniker füllt Formular aus
→ Büro liest das Formular
→ Büro überträgt die Daten nach WERBAS
```

Dadurch dokumentieren beide Rollen dieselben Informationen. CarTech reduziert den Aufwand des Mechanikers und gibt dem Büro einen strukturierten Datensatz zur Prüfung.

## Kernablauf

```text
Mechaniker spricht
→ Speech-to-Text erstellt ein Transkript
→ KI extrahiert strukturierte Entwurfsdaten
→ Mechaniker prüft und bestätigt
→ Büro prüft und ergänzt
→ Vorgang wird abgeschlossen
→ Büro übernimmt die Daten manuell nach WERBAS
```

Die KI darf ausschließlich explizit genannte oder eindeutig normalisierbare Werte übernehmen. Unsichere und fehlende Werte bleiben markiert; sie werden nicht geraten.

## Rollen und Verantwortlichkeiten

| Rolle | Verantwortung |
| --- | --- |
| Mechaniker | Startet den Vorgang, spricht Informationen ein, korrigiert die Ergebnisse bei Bedarf und bestätigt sie. |
| Büro | Prüft und korrigiert Daten, ordnet einen Kunden zu oder legt ihn an, ergänzt Verwaltungsdaten und schließt den Vorgang ab. |

Der Mechaniker erstellt keinen Kunden und erfasst keine administrativen Kundendaten. Ein Fahrzeug darf deshalb zunächst ohne `customer_id` bestehen. Die Kundenanlage oder -zuordnung erfolgt ausschließlich im Büro.

## Erfasste Informationen

### Fahrzeug

- Kennzeichen
- Kilometerstand
- Hersteller und Modell, sofern genannt
- Fahrgestellnummer (später beziehungsweise optional)

### Reifensatz

- Reifenart
- Reifengröße
- Hersteller und Modell
- Anzahl
- Profiltiefe je Achse oder Radposition
- Zustände wie Verschleiß oder Beschädigung

### Servicevorgang

- Vorgangstyp
- zusätzliche Notizen
- Datum und Mechaniker

Bei einem saisonalen Reifenwechsel können mehrere Reifensätze vorkommen. Jeder Satz erhält im Vorgang eine explizite Rolle: `installed`, `removed` oder `stored`. So wird ein eingelagerter Satz nicht mit dem montierten Satz verwechselt.

## Qualitäts- und Prüfprinzipien

- Sprachaufnahme ist der primäre Eingabekanal; kurze Korrekturen per Sprache oder Touch bleiben möglich.
- Die Mechanikeransicht zeigt nur die wichtigsten Informationen und eine klar erkennbare Bestätigungsaktion.
- Unsichere Angaben und Plausibilitätsfehler benötigen eine Prüfung, ändern Werte aber nicht automatisch.
- Das Originaltranskript und die ursprüngliche KI-Extraktion bleiben für die Nachvollziehbarkeit erhalten.
- Das Büro kann einzelne Felder korrigieren, ohne den gesamten Vorgang neu einzugeben.

## Statusmodell

Der Vorgangsstatus beschreibt nur den Ablauf, nicht die Qualität einzelner Werte:

```text
draft
→ mechanic_review
→ office_review
→ completed
```

Ein abgebrochener Vorgang kann den Status `rejected` erhalten. Fehlende, unsichere oder unplausible Werte werden separat über Feldstatus und `review_required` dargestellt.

## Abgrenzung des MVP

Nicht Teil des MVP sind:

- direkte WERBAS-Integration
- automatische Übernahme nach WERBAS
- native Smartphone-App
- eigene Speech-to-Text-Engine
- Microservices oder Kubernetes

Bestehende Kunden und eine WERBAS-Anbindung sind sinnvolle spätere Erweiterungen. Der MVP bleibt jedoch auch ohne diese Integration nutzbar.
