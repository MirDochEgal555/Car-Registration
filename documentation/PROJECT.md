# Fahrzeug- & Reifenerfassung – Projektübersicht

## Ziel

Das Projekt unterstützt die Werkstatt CarTech bei der Fahrzeugaufnahme sowie der Dokumentation von Reifenwechseln und Reifeneinlagerungen. Mechaniker erfassen Informationen per Sprache, prüfen das Ergebnis und senden den Vorgang in der Web-App ab. Der Datensatz wird danach zentral gespeichert und in der Büro-Inbox bereitgestellt.

Der MVP umfasst zwei Werkstattprotokolle:

- Reifenwechselprotokoll
- Reifeneinlagerungsprotokoll

Die Kundenanlage ist kein eigenes Werkstattprotokoll. Sie erfolgt bei Bedarf ausschließlich im Büro, nachdem ein Fahrzeug über eines der beiden Protokolle erfasst wurde.

## Ausgangslage

Der bisherige Ablauf ist papierbasiert:

```text
Mechaniker füllt Formular aus
→ Büro liest das Formular
→ Daten liegen verteilt auf Papier und in Folgesystemen vor
```

Dadurch dokumentieren beide Rollen dieselben Informationen. Die Anwendung reduziert den Aufwand des Mechanikers und gibt dem Büro einen strukturierten Datensatz zur Prüfung.

## Kernablauf

```text
Mechaniker spricht
→ Speech-to-Text erstellt ein Transkript
→ KI extrahiert strukturierte Entwurfsdaten
→ Mechaniker prüft, bestätigt und sendet ab
→ Datensatz wird zentral gespeichert
→ Büro erhält einen E-Mail-Hinweis und sieht den Vorgang als Neu in der Inbox
→ Büro prüft, korrigiert und ergänzt
→ Vorgang wird als Erledigt abgeschlossen
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

Im Reifenwechselprotokoll können der montierte und der demontierte Reifensatz vorkommen. Sie erhalten jeweils die explizite Rolle `installed` oder `removed`.

### Reifenwechselprotokoll

Das Reifenwechselprotokoll enthält Kunde, Datum, Fahrzeug, Erstzulassung (EZ), Kennzeichen, Vmax und Kilometerstand. Zusätzlich werden erfasst:

- Antriebsart E/Hybrid, RäWe sowie ausgeführte Arbeiten: Wuchten Stahl/Alu und maschinelle/manuelle Radwäsche
- WHM-Modus, nächster KD und nächster Ölservice
- Luftdruck-Mittelwert an Vorder- und Hinterachse, Felgenschloss, gleiche oder verschiedene Radschrauben und HU-Fälligkeit
- Winter- und Sommerräder jeweils getrennt: Profiltiefe, DOT, Größe, LI, VI, Hersteller und Profilbezeichnung
- Felgen- und Reifensichtprüfung mit i.O./n.i.O. und Position
- Fahrwerks- und Bremsensichtprüfung mit i.O./n.i.O.; bei n.i.O. die Bremsscheibendicke
- gereinigte Radnabe, RDKS (aktiv/passiv und angelernt), Limiter mit Aufkleber, Drehmoment, Unterschrift und WhatsApp-Freigabe

Damit Felgen- oder Reifenbefunde nicht dem falschen Radsatz zugeordnet werden, ist jede Sichtprüfung immer dem Winter- oder Sommersatz sowie gegebenenfalls einer Position zugeordnet.

Im Reifeneinlagerungsprotokoll werden die einzulagernden Reifensätze mit der Rolle `stored` erfasst. Eine Einlagerung bleibt damit ein eigenständiges Protokoll und wird nicht als Teil eines Reifenwechsels dokumentiert.

### Reifeneinlagerungsprotokoll

Das Einlagerungsprotokoll enthält zusätzlich zu Kunde, Datum, Fahrzeug und Kennzeichen folgende Angaben:

- Felgengröße sowie Felgenausführung: Alu, Stahl oder Original
- Felgenhersteller und Felgentyp
- für jeden einzelnen Reifen: Hersteller, Profil, Profiltiefe, DOT-Nummer, Gebrauchsspuren (Ja/Nein) und Beschädigungen
- Anmerkungen und Mechaniker
- Unterschrift des Kunden

Kunde, Fahrzeug und Kennzeichen werden über die vorhandenen Stammdaten referenziert. Profiltiefe, DOT-Nummer, Gebrauchsspuren und Beschädigungen werden je Reifen und nicht nur für den gesamten Satz gespeichert.

## Qualitäts- und Prüfprinzipien

- Sprachaufnahme ist der primäre Eingabekanal; kurze Korrekturen per Sprache oder Touch bleiben möglich.
- Die Mechanikeransicht zeigt nur die wichtigsten Informationen und eine klar erkennbare Bestätigungsaktion.
- Unsichere Angaben und Plausibilitätsfehler benötigen eine Prüfung, ändern Werte aber nicht automatisch.
- Das Originaltranskript und die ursprüngliche KI-Extraktion bleiben für die Nachvollziehbarkeit erhalten.
- Das Büro kann jedes fachliche Feld korrigieren, ohne den gesamten Vorgang neu einzugeben; unsichere, fehlende und unplausible Felder sind dabei klar markiert.
- Bei jedem Absenden erhält das Büro zusätzlich eine kurze E-Mail mit Kennzeichen, Absendezeitpunkt und einem authentifizierten Link zum Datensatz.

## Statusmodell

Der Vorgangsstatus beschreibt nur den Ablauf, nicht die Qualität einzelner Werte:

```text
draft
→ mechanic_review
→ new          (Büro-Inbox: Neu)
→ in_review    (Büro-Inbox: Prüfen)
→ completed
```

`completed` wird in der Büro-Inbox als **Erledigt** angezeigt. Ein abgebrochener Vorgang kann den Status `rejected` erhalten. Fehlende, unsichere oder unplausible Werte werden separat über Feldstatus und `review_required` dargestellt; sie sind kein Grund, den Vorgang aus der Inbox auszublenden.

## Abgrenzung des MVP

Nicht Teil des MVP sind:

- direkte WERBAS-Integration
- manuelle oder automatische Übergabe an WERBAS als Teil des Produktablaufs
- native Smartphone-App
- eigene Speech-to-Text-Engine
- Microservices oder Kubernetes

Eine WERBAS-Anbindung ist eine spätere Erweiterung. Der MVP bereitet sie ausschließlich durch eine saubere, erweiterbare Datenstruktur vor und bleibt vollständig ohne WERBAS-Integration nutzbar.
