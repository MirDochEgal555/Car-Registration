# Fahrzeug- & Reifenerfassung – Tech-Stack und Kosten

## Ziel

Die Anwendung unterstützt die Werkstatt CarTech bei der Voice-first-Fahrzeug- und Reifenerfassung. Der MVP unterstützt zwei Werkstattprotokolle: Reifenwechsel und Reifeneinlagerung.

```text
Mechaniker wählt ein Protokoll und spricht
→ KI strukturiert Daten
→ Mechaniker bestätigt und sendet ab
→ Datensatz wird zentral gespeichert
→ Büro erhält E-Mail-Hinweis und prüft in der Inbox
→ Vorgang wird erledigt
```

## Empfohlener Tech-Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Progressive Web App (PWA)

Die PWA läuft auf Smartphone, Tablet und Desktop, benötigt keine App-Store-Veröffentlichung und kann eine gemeinsame Anwendung für Mechaniker und Büro bereitstellen.

Geplante Bereiche:

- `/mechanic`
- `/office`

### Backend

- Python
- FastAPI
- SQLAlchemy

Aufgaben des Backends:

- Audiodateien annehmen
- Speech-to-Text ausführen
- strukturierte KI-Extraktion durchführen
- Daten validieren und zur Prüfung markieren
- abgesendete Vorgänge zentral und dauerhaft speichern
- Büro-Inbox nach `new`, `in_review` und `completed` bereitstellen
- E-Mail-Benachrichtigungen nach erfolgreichem Absenden auslösen und wiederholbar zustellen
- REST-API bereitstellen
- Datenbankzugriff verwalten

### Datenbank

- PostgreSQL

Kernobjekte:

- `Customer`
- `Vehicle`
- `ServiceRecord`
- `TireSet`
- `ServiceTireSet`
- `TireInspection`
- `TireCondition`

WERBAS-spezifische IDs bleiben im MVP leer und können später ergänzt werden; es gibt keine WERBAS-Integration und keine Übergabe im Produktablauf. Die vollständige Struktur ist im [Datenmodell](DATA_MODEL.md) beschrieben.

## Voice- und KI-Pipeline

```text
Audio
→ Speech-to-Text
→ Transkript
→ strukturierte KI-Extraktion
→ Entwurfsdaten und Feldstatus
→ Validierung
→ Mechanikerprüfung
→ Absenden und zentrale Speicherung
→ Büro-Inbox und E-Mail-Benachrichtigung
→ Büroprüfung
→ finaler Datensatz
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

Unsichere Werte werden nicht ergänzt. Feldstatus und Validierungsbedarf werden getrennt vom Vorgangsstatus gespeichert:

```json
{
  "model": null,
  "field_status": {
    "model": "uncertain"
  },
  "review_required": true
}
```

Optionale Confidence-Werte können zusammen mit ihrer Quelle gespeichert werden:

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
- PostgreSQL auf demselben Server für den MVP

## Empfohlene Entwicklungsreihenfolge

1. Datenmodell definieren
2. Mechaniker-UI erstellen
3. grundlegende Büroprüfung für manuell erfasste Vorgänge erstellen
4. Audioaufnahme und Speech-to-Text parallel integrieren
5. strukturierte KI-Extraktion implementieren
6. Validierungslogik ergänzen
7. Mechaniker-Bestätigung umsetzen
8. zentrale Speicherung, Büro-Inbox und E-Mail-Benachrichtigung umsetzen
9. Büroprüfung um KI-Daten, Transkript und Unsicherheiten erweitern
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
- manuelle oder automatische WERBAS-Übergabe als Teil des MVP-Ablaufs
- native Smartphone-App

Diese Technologien erhöhen die Komplexität, ohne für den MVP notwendig zu sein.

## Kosten

| Kostenpunkt | Erwartete Kosten |
| --- | --- |
| VPS / Hosting | ca. 5–15 € pro Monat |
| PostgreSQL | 0 € bei Self-Hosting |
| Domain | ca. 10–20 € pro Jahr |
| HTTPS / SSL | 0 € |
| Speech-to-Text-API | wenige Euro bis ca. 20 € pro Monat |
| KI-Datenextraktion | wenige Euro pro Monat |
| React, FastAPI und PostgreSQL | 0 € |
| Docker, Caddy oder Nginx | 0 € |
| PWA | 0 € |
| WERBAS-Integration | nicht im MVP enthalten |

Für eine kleine Werkstatt sind Gesamtkosten von etwa 10–30 € pro Monat realistisch; als Zielwert für den MVP gelten etwa 15–25 € pro Monat. Die tatsächlichen KI-Kosten hängen vor allem von der Zahl der Aufnahmen, der Audiolänge sowie den verwendeten Speech-to-Text- und KI-Modellen ab.
