# Fahrzeug- & Reifenerfassung – Tech-Stack und Kosten

## Ziel

Die Anwendung unterstützt die Werkstatt CarTech bei der Voice-first-Fahrzeug- und Reifenerfassung. Der MVP unterstützt zwei Werkstattprotokolle: Reifenwechsel und Reifeneinlagerung.

```text
Mechaniker wählt ein Protokoll und spricht
→ KI strukturiert Daten
→ Mechaniker bestätigt und sendet ab
→ Büro erhält das strukturierte Protokoll per E-Mail
→ Büro prüft, korrigiert und speichert in WERBAS
```

## Empfohlener Tech-Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Progressive Web App (PWA)

Die PWA läuft auf Smartphone, Tablet und Desktop und benötigt keine App-Store-Veröffentlichung. Im MVP ist sie die Eingabeoberfläche für Mechaniker.

Geplante Bereiche:

- `/mechanic`

`/office` ist eine optionale spätere Erweiterung; im MVP arbeitet das Büro in WERBAS.

### Backend

- Python
- FastAPI

Aufgaben des Backends:

- Audiodateien annehmen
- Speech-to-Text ausführen
- strukturierte KI-Extraktion durchführen
- Daten validieren und zur Prüfung markieren
- den strukturierten E-Mail-Text erzeugen und an die konfigurierte Büro-Adresse versenden
- REST-API bereitstellen

### E-Mail-Versand

- SMTP oder ein transaktionaler E-Mail-Dienst
- Versandstatus an die Mechaniker-Web-App zurückgeben
- bei Fehlern erneutes Absenden aus der laufenden Sitzung erlauben

### Optionale Datenbank und Büro-Oberfläche

Für eine spätere zentrale Speicherung und Büro-Inbox:

- PostgreSQL
- SQLAlchemy
- `Customer`
- `Vehicle`
- `ServiceRecord`
- `TireSet`
- `ServiceTireSet`
- `TireInspection`
- `TireCondition`

WERBAS bleibt im MVP das führende Speichersystem. Die E-Mail wird dort manuell übernommen; es gibt keine direkte API-Integration. Die vollständige, auch für eine spätere zentrale Speicherung geeignete Struktur ist im [Datenmodell](DATA_MODEL.md) beschrieben.

## Voice- und KI-Pipeline

```text
Audio
→ Speech-to-Text
→ Transkript
→ strukturierte KI-Extraktion
→ Entwurfsdaten und Feldstatus
→ Validierung
→ Mechanikerprüfung
→ strukturierte E-Mail an das Büro
→ manuelle Prüfung und Speicherung in WERBAS
```

Beispiel für eine Eingabe:

> „KA AB 123, Kilometer 82.430, vier Michelin Alpin 6 Winterreifen, 205 55 R16, vorne sechs Millimeter, hinten fünf, hinten rechts leicht außen abgefahren.“

Extrahierter Entwurf:

```json
{
  "license_plate": "KA-AB 123",
  "mileage_km": 82430,
  "tire_type": "winter",
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16,
  "manufacturer": "Michelin",
  "model": "Alpin 6",
  "quantity": 4,
  "tread_front_mm": 6,
  "tread_rear_mm": 5,
  "conditions": [
    {
      "condition": "outer_wear",
      "position": "rear_right"
    }
  ]
}
```

Unsichere Werte werden nicht ergänzt. Feldstatus und Validierungsbedarf werden im E-Mail-Abschnitt „Prüfhinweise“ ausgegeben:

```json
{
  "model": null,
  "field_status": {
    "model": "uncertain"
  },
  "review_required": true
}
```

Optionale Confidence-Werte können im strukturierten Entwurf zusammen mit ihrer Quelle ausgegeben werden:

```json
{
  "value": "Michelin",
  "confidence": 0.98,
  "source": "speech"
}
```

## Bereitstellung

- Docker
- kleiner VPS
- Caddy oder Nginx als Reverse Proxy
- HTTPS
- Zugang zu einem E-Mail-Dienst oder SMTP-Server

## Empfohlene Entwicklungsreihenfolge

1. Datenmodell definieren
2. Mechaniker-UI erstellen
3. E-Mail-Template für die strukturierte Ausgabe erstellen
4. Audioaufnahme und Speech-to-Text parallel integrieren
5. strukturierte KI-Extraktion implementieren
6. Validierungslogik ergänzen
7. Mechaniker-Bestätigung umsetzen
8. E-Mail-Versand, Fehleranzeige und Wiederholen umsetzen
9. E-Mail-Ausgabe mit WERBAS-Eingabe im Büro testen
10. Testbetrieb in der Werkstatt durchführen

Der Schwerpunkt liegt auf zuverlässiger Extraktion, nachvollziehbarer Validierung und einer schnellen Bestätigungsoberfläche.

## Nicht im MVP erforderlich

- Flutter
- React Native
- Kubernetes
- Microservices
- MongoDB
- eigene Speech-to-Text-Engine
- direkte WERBAS-Integration
- zentrale Speicherung in der CarTech-Anwendung
- Büro-Inbox oder Büro-Bearbeitung in der CarTech-Web-App
- native Smartphone-App

Diese Technologien erhöhen die Komplexität, ohne für den MVP notwendig zu sein.

## Kosten

| Kostenpunkt | Erwartete Kosten |
| --- | --- |
| VPS / Hosting | ca. 5–15 € pro Monat |
| E-Mail-Versand | je nach SMTP- oder E-Mail-Dienst, meist wenige Euro pro Monat |
| Domain | ca. 10–20 € pro Jahr |
| HTTPS / SSL | 0 € |
| Speech-to-Text-API | wenige Euro bis ca. 20 € pro Monat |
| KI-Datenextraktion | wenige Euro pro Monat |
| React und FastAPI | 0 € |
| Docker, Caddy oder Nginx | 0 € |
| PWA | 0 € |
| direkte WERBAS-Integration | nicht im MVP enthalten |

Für eine kleine Werkstatt sind Gesamtkosten von etwa 10–30 € pro Monat realistisch; als Zielwert für den MVP gelten etwa 15–25 € pro Monat. Die tatsächlichen KI-Kosten hängen vor allem von der Zahl der Aufnahmen, der Audiolänge sowie den verwendeten Speech-to-Text- und KI-Modellen ab.
