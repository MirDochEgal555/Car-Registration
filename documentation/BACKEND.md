# Backend-Dokumentation

## Zweck und Einordnung

Das Backend ist der technische Übergabepunkt zwischen der Web-App des Mechanikers und dem Büro. Es verarbeitet `tire_change` (Reifenwechsel) und `tire_storage` (Reifeneinlagerung).

WERBAS bleibt im MVP das fachlich führende System. CarTech unterhält keine zentrale Kunden-, Fahrzeug- oder Vorgangsdatenbank: Es prüft browserseitige Entwürfe, erzeugt eine strukturierte Büro-E-Mail und hält bestätigte Versandaufträge in einer kleinen SQLite-Outbox vor. So geht ein Vorgang bei SMTP-Fehlern nicht still verloren.

Sprachverarbeitung und KI-Extraktion liegen vor diesem Backend und sind hier nicht implementiert. Sie müssen einen `RegistrationDraft` gemäß API-Vertrag erzeugen.

Fachliche Felddefinitionen stehen im [Datenmodell](DATA_MODEL.md); lokale Startanweisungen enthält das [Backend-README](../src/backend/README.md).

## Architektur

```text
Web-App / Extraktion
        |
        | vollständiger RegistrationDraft
        v
FastAPI-Routen (/api/v1/registrations)
        |
        +-- Validierung und Kennzeichen-Normalisierung
        |       |
        |       +-- Ergebnis für die Mechanikerprüfung
        |
        +-- bestätigter Versand
                |
                +-- SQLite-Outbox (dauerhaft, ohne Rohtranskript)
                +-- E-Mail-Renderer (Text + HTML aus einem Dokument)
                +-- SMTP-Server --> Büro / WERBAS
```

| Baustein | Aufgabe |
| --- | --- |
| `app/main.py` | Erstellt die FastAPI-Anwendung und stellt beim Start unterbrochene Versandversuche wieder retry-fähig. |
| `app/api/v1/routes/registrations.py` | Stellt Validierung, Versand, Statusabfrage und Wiederholung bereit. |
| `app/models/registration.py` | Beschreibt API-Vertrag für browserseitige Entwürfe und Versandantworten. |
| `app/services/registration_validation.py` | Enthält fachliche Plausibilitäts- und Ablaufprüfungen. |
| `app/services/delivery_store.py` | Implementiert die lokale, persistente SQLite-Outbox mit atomaren Statuswechseln. |
| `app/services/registration_email.py` | Baut Text- und HTML-E-Mail aus demselben Präsentationsmodell. |
| `app/services/email.py` | Kapselt SMTP, TLS/SSL und Konfigurationsfehler. |

Die Klassen in `app/models/schemas.py` beschreiben ein optionales Zieldatenmodell für eine spätere zentrale Speicherung. Sie sind keine aktuell verwendeten Datenbankmodelle.

## API und Ablauf

Alle Endpunkte sind unter `/api/v1` versioniert.

| Methode und Pfad | Zweck | Persistenz |
| --- | --- | --- |
| `GET /health` | Liveness-Prüfung der Anwendung | keine |
| `POST /registrations/validate` | Prüft einen vollständigen Entwurf für die Mechanikeransicht und normalisiert ein vorhandenes Kennzeichen. | keine |
| `POST /registrations/send` | Prüft erneut, verlangt Mechanikerbestätigung, legt den Vorgang ab und versucht den E-Mail-Versand. | SQLite-Outbox |
| `GET /registrations/{id}/delivery-status` | Liefert Versandstatus, Versuchszähler und sichere Fehlermeldung ohne Protokolldaten. | liest Outbox |
| `POST /registrations/{id}/retry` | Versendet den unveränderten gespeicherten Vorgang erneut. | aktualisiert Outbox |

Ein minimal versandfähiger Entwurf enthält diese vier fachlichen Pflichtwerte:

```json
{
  "service_type": "tire_storage",
  "service_date": "2026-08-23",
  "mechanic_id": "3c0a5fe3-b1b7-4f9f-a9e0-4fc653c2a96e",
  "mechanic_confirmed": true,
  "vehicle": { "license_plate": "CW-AB 123" }
}
```

`POST /registrations/send` liefert `422`, wenn `mechanic_confirmed` nicht `true` ist, und `409`, wenn Pflichtwerte fehlen oder Werte unplausibel sind. Bei SMTP- oder Konfigurationsfehlern bleibt der Vorgang gespeichert; die Antwort `502` beziehungsweise `503` enthält den Status und einen Retry-Pfad.

## Validierung und Prüfhinweise

Die Validierung arbeitet auf einer tiefen Kopie des Entwurfs. Sie speichert weder Entwürfe noch verändert sie den Browserzustand. Eine vorhandene deutsche Kennzeichen-Schreibweise wird konsistent normalisiert, etwa `cw ab 123` zu `CW-AB 123`.

Neben den Pflichtangaben prüft das Backend unter anderem:

- keine Zukunftsdaten für `service_date`;
- plausible Zahlenbereiche für Kilometerstand, Reifengröße, Profiltiefe, Luftdruck, Drehmoment und Bremsscheibendicke;
- passende Reifensatzrollen: beim Reifenwechsel `installed` oder `removed`, bei der Einlagerung `stored`;
- eine konkrete Radposition bei auffälligen Sichtprüfungen und Bremsscheibenmessungen;
- Wechseldetails ausschließlich bei `tire_change` und dort die Angabe, ob ein Räderwechsel durchgeführt wurde.

`field_status` trennt die fachliche Versandfähigkeit von Prüfhinweisen:

| Feldstatus | Wirkung |
| --- | --- |
| `missing` | Bei Pflichtwerten nicht versandfähig; bei optionalen Werten nur sichtbar. |
| `invalid` | `review_required: true`; vom Backend festgestellte ungültige Pflicht- oder Plausibilitätswerte verhindern den Versand. |
| `uncertain` | `review_required: true`, aber allein kein Versandhindernis. |
| `valid` | Kein Prüfhinweis. |

Extraktionsmarkierungen bleiben erhalten. So kann der Mechaniker eine unsichere, aber nach Sichtprüfung akzeptierte Angabe bewusst versenden; sie erscheint dann in den E-Mail-Prüfhinweisen.

## Versand-Outbox und Zustände

Vor dem SMTP-Aufruf speichert das Backend die validierte, bestätigte Registrierung. Das Rohtranskript wird dabei ausdrücklich entfernt. Die Vorgangs-UUID ist ein Idempotenzschlüssel: dieselbe ID mit demselben strukturierten Inhalt wird nicht erneut angelegt; dieselbe ID mit anderen Inhalten führt zu `409 Conflict`.

| Zustand | Bedeutung | Nächster Übergang |
| --- | --- | --- |
| `mechanic_review` | Ergebnis einer reinen Validierung; noch nicht gespeichert. | Bestätigung und Versand |
| `email_pending` | Bestätigter Auftrag ist dauerhaft gespeichert. | `email_sending` |
| `email_sending` | Ein Request besitzt den Versandversuch. | `email_sent` oder `email_failed` |
| `email_sent` | Der konfigurierte SMTP-Server hat die Nachricht angenommen. | final |
| `email_failed` | Konfiguration, Verbindung, Versand oder Rendering ist fehlgeschlagen. | erneuter Versuch |

Der Übergang nach `email_sending` ist innerhalb der SQLite-Outbox atomar. Beim Anwendungsstart werden verbliebene `email_sending`-Einträge zu `email_failed`, damit sie erneut versendet werden können. Wiederholungen erfolgen nicht automatisch: Web-App oder Betriebssystem müssen den Retry-Endpunkt gezielt aufrufen.

Die Zustellgarantie endet bei der Annahme durch den SMTP-Server. Fällt der Prozess nach erfolgreicher SMTP-Annahme, aber vor `email_sent` aus, bleibt ein Eintrag als laufend beziehungsweise später fehlgeschlagen zurück. Ein erneuter Versand kann dann eine doppelte E-Mail erzeugen. Die Implementierung bietet damit eine robuste *at-least-once*-Übergabe mit üblicher Idempotenz im Normalfall, keine technisch garantierte Exactly-once-Zustellung.

## E-Mail und Konfiguration

Die E-Mail enthält eine Text- und eine HTML-Alternative (`multipart/alternative`). Beide Varianten werden aus einem gemeinsamen Dokument gerendert; Feldwerte und Prüfhinweise können daher nicht auseinanderlaufen. Werte werden für HTML maskiert. Das Rohtranskript ist weder in der E-Mail noch in der Outbox enthalten.

Die Konfiguration wird ausschließlich aus Prozess-Umgebungsvariablen gelesen. Eine lokale `.env`-Datei wird nicht automatisch geladen; die Deployment-Umgebung muss die Werte bereitstellen. Eine kommentierte Vorlage liegt unter [`src/backend/.env.example`](../src/backend/.env.example).

| Variable | Bedeutung |
| --- | --- |
| `CARTECH_OFFICE_EMAIL` | Empfängeradresse des Büros; ohne sie bleibt der Auftrag retry-fähig gespeichert. |
| `CARTECH_SMTP_HOST`, `CARTECH_SMTP_PORT` | SMTP-Ziel; Port `587` ist der Standard. |
| `CARTECH_SMTP_FROM` | Absenderadresse; zusammen mit dem Host für den Versand erforderlich. |
| `CARTECH_SMTP_USERNAME`, `CARTECH_SMTP_PASSWORD` | Entweder beide gesetzt oder beide leer. |
| `CARTECH_SMTP_USE_TLS` | STARTTLS, standardmäßig `true`. |
| `CARTECH_SMTP_USE_SSL` | Implizites TLS, typischerweise für Port `465`; STARTTLS wird dann nicht verwendet. |
| `CARTECH_SMTP_TIMEOUT_SECONDS` | Positiver Verbindungs- und Versand-Timeout, standardmäßig `15`. |
| `CARTECH_DELIVERY_STORE_PATH` | Speicherort der SQLite-Outbox, standardmäßig `data/processed/cartech-deliveries.sqlite3`. |

Für Produktion muss das Outbox-Verzeichnis persistent, verschlüsselt und auf die Anwendung beschränkt sein. Es enthält strukturierte Fahrzeug- und Werkstattdaten. Zugangsdaten gehören in ein Secret-Management des Deployments, nicht in das Repository.

## Kohärenzbewertung

Der aktuelle Backend-Stand ist für den definierten MVP fachlich und technisch kohärent:

- Der Client besitzt den Entwurf; das Backend validiert ihn vor jeder Übergabe erneut.
- Validierung, E-Mail-Darstellung und Outbox verwenden denselben strukturierten Vertrag.
- Der kritische Fehlerfall „E-Mail nicht erreichbar“ ist durch Speichern vor dem SMTP-Aufruf und durch Retry abgedeckt.
- Das Rohtranskript bleibt aus der dauerhaften Versandablage und aus der E-Mail heraus.
- Die Test-Suite deckt Konfiguration, Modelle, Validierung, E-Mail-Rendering, Outbox, Fehlerfälle und die dokumentierten Werkstattfälle ab. Bei der Prüfung dieses Stands liefen `61` Tests erfolgreich durch.

Folgende Punkte sind bewusste MVP-Grenzen oder vor einem Produktivbetrieb zu entscheiden:

1. **Authentifizierung und Berechtigungen fehlen.** `mechanic_id` wird vom Client geliefert, und alle Endpunkte sind ohne Zugriffsschutz erreichbar. Vor einem Netzwerkbetrieb sind Identität, Rollenprüfung und HTTPS über einen Reverse Proxy erforderlich.
2. **SQLite ist für eine einzelne Instanz gedacht.** Mehrere App-Instanzen brauchen mindestens einen gemeinsam nutzbaren, zuverlässig sperrenden Speicher; für eine skalierte Produktion ist eine zentrale Outbox-Datenbank wie PostgreSQL sinnvoller.
3. **Versandüberwachung fehlt.** Es gibt keine automatische Retry-Strategie, keine Alarmierung und keinen Readiness-Check für Outbox oder SMTP. Der vorhandene Health-Endpunkt ist ausschließlich ein Liveness-Check.
4. **Aufbewahrung und Datenschutz sind noch keine Funktion.** Ein Löschkonzept, Backups, Verschlüsselung, Zugriffsprotokollierung und eine definierte Aufbewahrungsdauer müssen betrieblich festgelegt werden.
5. **Reifensatzrollen sind nicht eindeutig begrenzt.** Die Validierung prüft, ob eine Rolle zum Protokolltyp passt, erlaubt aber mehrere Sätze mit derselben Rolle. Falls je Rolle genau ein Satz vorgesehen ist, sollte dies validiert werden. Falls mehrere erlaubt sein sollen, brauchen Prüfungen statt der Rolle eine stabile Reifensatz-ID als Referenz.

Nicht Teil des Backends sind aktuell die Speech-to-Text-/KI-Anbindung, eine direkte WERBAS-Schnittstelle, eine zentrale CarTech-Fachdatenbank und eine Büro-Oberfläche. Diese Erweiterungen können auf dem vorhandenen API- und Zieldatenmodell aufbauen, sollten die genannten Produktionsentscheidungen aber zuerst berücksichtigen.

## Lokale Prüfung

Aus `src/backend`:

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest -q
uvicorn app.main:app --reload
```

Danach ist die Liveness-Prüfung unter `http://127.0.0.1:8000/api/v1/health` und die interaktive OpenAPI-Dokumentation unter `http://127.0.0.1:8000/docs` verfügbar.
