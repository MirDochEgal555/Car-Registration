# Backend-Dokumentation

## Zweck und Einordnung

Das Backend ist der technische Übergabepunkt zwischen der Web-App des Mechanikers und dem Büro. Es verarbeitet `tire_change` (Reifenwechsel) und `tire_storage` (Reifeneinlagerung).

WERBAS bleibt im MVP das fachlich führende System. CarTech unterhält keine zentrale Kunden-, Fahrzeug- oder Vorgangsdatenbank: Es prüft browserseitige Entwürfe, erzeugt eine strukturierte Büro-E-Mail und hält bestätigte Versandaufträge in einer kleinen SQLite-Outbox vor. So geht ein Vorgang bei SMTP-Fehlern nicht still verloren.

Die Speech-to-Text-Anbindung ist über `POST /audio/transcribe` integriert und liefert ausschließlich ein Rohtranskript. Die nachgelagerte Phase-7-Pipeline ist über `POST /extractions` integriert: Sie erzeugt aus diesem Transkript einen geprüften `RegistrationDraft` gemäß API-Vertrag.

Fachliche Felddefinitionen stehen im [Datenmodell](DATA_MODEL.md); lokale Startanweisungen enthält das [Backend-README](../src/backend/README.md).

## Architektur

```text
Web-App / Audioaufnahme
        |
        +-- POST /audio/transcribe --> unverändertes Transkript
        |
        +-- POST /extractions --> Strict Structured Output
                                  --> Normalisierung und Fachvalidierung
                                  --> RegistrationDraft + field_status
        |
        +-- POST /registrations/validate --> Mechanikerprüfung
        |
        +-- bestätigter Versand
                |
                +-- SQLite-Outbox (dauerhaft, mit Rohtranskript)
                +-- E-Mail-Renderer (Text + HTML aus einem Dokument)
                +-- SMTP-Server --> Büro / WERBAS
```

| Baustein | Aufgabe |
| --- | --- |
| `app/main.py` | Erstellt die FastAPI-Anwendung und stellt beim Start unterbrochene Versandversuche wieder retry-fähig. |
| `app/api/v1/routes/extraction.py` | Führt die Phase-7-Extraktionspipeline über die öffentliche API aus. |
| `app/api/v1/routes/registrations.py` | Stellt Validierung, Versand, Statusabfrage und Wiederholung bereit. |
| `app/models/registration.py` | Beschreibt API-Vertrag für browserseitige Entwürfe und Versandantworten. |
| `app/models/extraction.py` | Definiert das strikte KI-Structured-Output-Schema mit Wert und Feldstatus. |
| `app/services/extraction_provider.py` | Kapselt den OpenAI-Structured-Outputs-Aufruf und die sichere Fehlergrenze. |
| `app/services/extraction_normalization.py` / `extraction_validation.py` | Normalisieren und validieren ausschließlich explizit gelieferte Extraktionswerte. |
| `app/services/extraction_mapping.py` | Überführt den geprüften Structured Output verlustfrei in den vorhandenen `RegistrationDraft`. |
| `app/services/registration_validation.py` | Enthält fachliche Plausibilitäts- und Ablaufprüfungen. |
| `app/services/delivery_store.py` | Implementiert die lokale, persistente SQLite-Outbox mit atomaren Statuswechseln. |
| `app/services/registration_email.py` | Baut Text- und HTML-E-Mail aus demselben Präsentationsmodell. |
| `app/services/email.py` | Kapselt SMTP, TLS/SSL und Konfigurationsfehler. |

Die Klassen in `app/models/schemas.py` beschreiben ein optionales Zieldatenmodell für eine spätere zentrale Speicherung. Sie sind keine aktuell verwendeten Datenbankmodelle.

`POST /audio/transcribe` nimmt das `audio/webm`-Blob des Browser-`MediaRecorder`
als Multipart-Feld `audio` entgegen und übergibt es an den OpenAI-
Transkriptionsadapter. Erfolgreiche Antworten enthalten `status: "completed"`
und den unstrukturierten `transcript`. Fehlende, fehlerhafte, leere und nicht
unterstützte Dateien sowie fehlgeschlagene Transkriptionen liefern
`status: "failed"`, `transcript: null` und einen einheitlichen Fehlerkörper mit
`error.code` und `error.message`. Der Adapter übergibt die Sprache `de` sowie
deutschen Kfz-Werkstatt-Kontext und Fachbegriffe. Die Antwort bleibt bewusst
ein Rohtranskript; die Fahrzeug- oder Vorgangsextraktion läuft anschließend
explizit über `POST /extractions`.

## API und Ablauf

Alle Endpunkte sind unter `/api/v1` versioniert.

| Methode und Pfad | Zweck | Persistenz |
| --- | --- | --- |
| `GET /health` | Liveness-Prüfung der Anwendung | keine |
| `POST /audio/transcribe` | Prüft eine Browseraufnahme im Format `audio/webm` und transkribiert sie mit OpenAI. | keine |
| `POST /extractions` | Führt Transkript, strikte KI-Extraktion, Normalisierung, Fachvalidierung und Mapping in den `RegistrationDraft` zusammen. | keine |
| `POST /registrations/validate` | Prüft einen vollständigen Entwurf für die Mechanikeransicht und normalisiert ein vorhandenes Kennzeichen. | keine |
| `POST /registrations/send` | Prüft erneut, verlangt Mechanikerbestätigung, legt den Vorgang ab und versucht den E-Mail-Versand. | SQLite-Outbox |
| `GET /registrations/{id}/delivery-status` | Liefert Versandstatus, Versuchszähler und sichere Fehlermeldung ohne Protokolldaten. | liest Outbox |
| `POST /registrations/{id}/retry` | Versendet den unveränderten gespeicherten Vorgang erneut. | aktualisiert Outbox |

`POST /extractions` erwartet ausschließlich ein unverändertes Transkript:

```json
{ "transcript": "CW AB 123, vier Winterreifen." }
```

Die Route ruft den konfigurierten OpenAI-Adapter mit dem vorhandenen Strict-
Schema auf und gibt `ValidationResponse` zurück. Dessen `registration` ist der
geprüfte `RegistrationDraft`; `field_status` und `review_required` befinden
sich sowohl im Antwortumschlag als auch im Entwurf. Ein leerer Text ergibt
`422`, ein nicht verfügbarer Anbieter `503` und eine unbrauchbare
Anbieterantwort `502`. Die bestehende Audio-Route und die bestehenden
Registrierungsrouten bleiben dabei unverändert getrennt und rückwärtskompatibel.

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

Vor dem SMTP-Aufruf speichert das Backend die validierte, bestätigte Registrierung einschließlich des unveränderten Rohtranskripts. Das Transkript wird nie in die E-Mail gerendert und nach seiner Verarbeitung nicht erneut zur Ableitung strukturierter Werte verwendet. Die Vorgangs-UUID ist ein Idempotenzschlüssel: dieselbe ID mit demselben strukturierten Inhalt wird nicht erneut angelegt; dieselbe ID mit anderen Inhalten führt zu `409 Conflict`.

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

Die E-Mail enthält eine Text- und eine HTML-Alternative (`multipart/alternative`). Beide Varianten werden aus einem gemeinsamen Dokument gerendert; Feldwerte und Prüfhinweise können daher nicht auseinanderlaufen. Werte werden für HTML maskiert. Das unveränderte Rohtranskript bleibt aus der E-Mail heraus, wird aber zusammen mit dem bestätigten Vorgang in der Outbox für spätere Büroprüfung oder Fehlersuche aufbewahrt; es ist keine strukturierte Datenquelle.

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
| `CARTECH_OPENAI_API_KEY` | API-Schlüssel für Speech-to-Text und die strikte KI-Extraktion; alternativ wird der Standardname `OPENAI_API_KEY` gelesen. |
| `CARTECH_OPENAI_TRANSCRIPTION_MODEL` | OpenAI-Transkriptionsmodell, standardmäßig `gpt-transcribe`. |
| `CARTECH_OPENAI_EXTRACTION_MODEL` | OpenAI-Modell für Strict Structured Outputs in `POST /extractions`, standardmäßig `gpt-4o-mini`. |
| `CARTECH_OPENAI_TIMEOUT_SECONDS` | Positiver Request-Timeout für Speech-to-Text und KI-Extraktion, standardmäßig `30`. |

Für Produktion muss das Outbox-Verzeichnis persistent, verschlüsselt und auf die Anwendung beschränkt sein. Es enthält strukturierte Fahrzeug- und Werkstattdaten sowie Rohtranskripte. Zugangsdaten gehören in ein Secret-Management des Deployments, nicht in das Repository.

## Kohärenzbewertung

Der aktuelle Backend-Stand ist für den definierten MVP fachlich und technisch kohärent:

- Der Client kann einen Entwurf manuell pflegen; das Backend kann zusätzlich aus einem Transkript einen neuen, geprüften `RegistrationDraft` erzeugen. Beide Wege verwenden dieselbe anschließende Validierung.
- Validierung, E-Mail-Darstellung und Outbox verwenden denselben strukturierten Vertrag.
- Der kritische Fehlerfall „E-Mail nicht erreichbar“ ist durch Speichern vor dem SMTP-Aufruf und durch Retry abgedeckt.
- Das Rohtranskript wird unverändert zusammen mit dem Vorgang aufbewahrt, bleibt aber aus der E-Mail heraus und beeinflusst keine strukturierten Werte.
- Die Test-Suite deckt Konfiguration, Modelle, Transkription, strikte KI-Antworten, Normalisierung, Validierung, Mapping, E-Mail-Rendering, Outbox, Fehlerfälle und 33 dokumentierte Phase-7-Fälle ab. Bei der Prüfung dieses Stands liefen `182` Backend-Tests erfolgreich durch.

Folgende Punkte sind bewusste MVP-Grenzen oder vor einem Produktivbetrieb zu entscheiden:

1. **Authentifizierung und Berechtigungen fehlen.** `mechanic_id` wird vom Client geliefert, und alle Endpunkte sind ohne Zugriffsschutz erreichbar. Vor einem Netzwerkbetrieb sind Identität, Rollenprüfung und HTTPS über einen Reverse Proxy erforderlich.
2. **SQLite ist für eine einzelne Instanz gedacht.** Mehrere App-Instanzen brauchen mindestens einen gemeinsam nutzbaren, zuverlässig sperrenden Speicher; für eine skalierte Produktion ist eine zentrale Outbox-Datenbank wie PostgreSQL sinnvoller.
3. **Versandüberwachung fehlt.** Es gibt keine automatische Retry-Strategie, keine Alarmierung und keinen Readiness-Check für Outbox oder SMTP. Der vorhandene Health-Endpunkt ist ausschließlich ein Liveness-Check.
4. **Aufbewahrung und Datenschutz sind noch keine Funktion.** Ein Löschkonzept, Backups, Verschlüsselung, Zugriffsprotokollierung und eine definierte Aufbewahrungsdauer müssen betrieblich festgelegt werden.
5. **Reifensatzrollen sind nicht eindeutig begrenzt.** Die Validierung prüft, ob eine Rolle zum Protokolltyp passt, erlaubt aber mehrere Sätze mit derselben Rolle. Falls je Rolle genau ein Satz vorgesehen ist, sollte dies validiert werden. Falls mehrere erlaubt sein sollen, brauchen Prüfungen statt der Rolle eine stabile Reifensatz-ID als Referenz.

Nicht Teil des Backends sind aktuell eine direkte WERBAS-Schnittstelle, eine zentrale CarTech-Fachdatenbank und eine Büro-Oberfläche. Diese Erweiterungen können auf dem vorhandenen API- und Zieldatenmodell aufbauen, sollten die genannten Produktionsentscheidungen aber zuerst berücksichtigen.

## Lokale Prüfung

Aus `src/backend`:

```bash
python3 -m pip install -e '.[dev]'
python3 -m pytest -q
uvicorn app.main:app --reload
```

Danach ist die Liveness-Prüfung unter `http://127.0.0.1:8000/api/v1/health` und die interaktive OpenAPI-Dokumentation unter `http://127.0.0.1:8000/docs` verfügbar.
