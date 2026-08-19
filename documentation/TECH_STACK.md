# CarTech – Tech-Stack und Kosten

## Ziel

CarTech ist eine Voice-first-Anwendung zur Fahrzeug- und Reifenerfassung in kleinen Werkstätten. Der MVP unterstützt Neukundenaufnahmen und saisonale Reifenwechsel.

```text
Mechaniker spricht
→ KI strukturiert Daten
→ Mechaniker bestätigt
→ Büro prüft
→ Büro übernimmt Daten manuell nach WERBAS
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

WERBAS-spezifische IDs bleiben im MVP leer und können später ergänzt werden. Die vollständige Struktur ist im [Datenmodell](DATA_MODEL.md) beschrieben.

## Voice- und KI-Pipeline

```text
Audio
→ Speech-to-Text
→ Transkript
→ strukturierte KI-Extraktion
→ Entwurfsdaten und Feldstatus
→ Validierung
→ Mechanikerprüfung
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
8. Büroprüfung um KI-Daten, Transkript und Unsicherheiten erweitern
9. Testbetrieb in der Werkstatt durchführen
10. bestehende Kunden und WERBAS integrieren

Der Schwerpunkt liegt auf zuverlässiger Extraktion, nachvollziehbarer Validierung und einer schnellen Bestätigungsoberfläche.

## Nicht im MVP erforderlich

- Flutter
- React Native
- Kubernetes
- Microservices
- MongoDB
- eigene Speech-to-Text-Engine
- direkte WERBAS-Integration
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
| WERBAS-Integration | im MVP 0 € |

Für eine kleine Werkstatt sind Gesamtkosten von etwa 10–30 € pro Monat realistisch; als Zielwert für den MVP gelten etwa 15–25 € pro Monat. Die tatsächlichen KI-Kosten hängen vor allem von der Zahl der Aufnahmen, der Audiolänge sowie den verwendeten Speech-to-Text- und KI-Modellen ab.
