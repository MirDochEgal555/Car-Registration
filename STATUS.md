# Projektstatus

**Stand: 16.09.2026**

## Kurz gesagt

Die digitale Erfassung für Reifenwechsel und Reifeneinlagerung ist umgesetzt. Mitarbeitende können Vorgänge erfassen, Angaben prüfen und sie nach Bestätigung an das Büro weitergeben. Die Spracheingabe mit angezeigtem Transkript sowie die automatische Phase‑7-Übernahme in einen geprüften, bearbeitbaren Entwurf sind umgesetzt.

`POST /api/v1/extractions` verarbeitet ein Transkript über Strict Structured Output, Normalisierung und Validierung zum vorhandenen `RegistrationDraft`. Unsichere und ungültige Angaben bleiben mit den bestehenden Feldstatus sichtbar; `review_required` wird aus dem finalen Statussatz abgeleitet. Die technische Abdeckung umfasst 33 dokumentierte API-Fälle.

Eine Demo der Oberfläche ist online. Die vollständige Nutzung mit Prüfung, E-Mail-Versand und Versandstatus benötigt noch eine eingerichtete Betriebsumgebung.

## Noch zu programmieren

- Die Betriebsumgebung für Backend, SMTP, persistente Outbox, HTTPS und Zugriffsrechte einrichten.
- Die Online-Demo mit dem öffentlich erreichbaren Backend verbinden.

## Noch zu reviewen und testen

- Phase-8-Fachabnahme: 30–50 anonymisierte echte Werkstattformulierungen, einschließlich Dialekt, Versprecher und Selbstkorrekturen.
- Prüfen, dass Unsicherheiten, Widersprüche und ungültige Werte in der Mechanikeransicht verständlich angezeigt und korrigiert werden.
- Sprachaufnahme, KI-Extraktion, Versand und Retry auf Smartphone/Tablet unter Werkstattbedingungen end-to-end testen.
- Mit der Werkstatt festlegen und freigeben, welche Felder je Protokoll verpflichtend sind.

## Nächster Schritt – Pilotbetrieb

Die Phase-8-Fachabnahme mit realistischen Werkstattaufnahmen starten und die Betriebsumgebung für den geschützten Werkstatt-Pilot einrichten. Der Hauptablauf „sprechen → KI-Entwurf prüfen → senden“ ist nun Voice-first nutzbar.

## Hinweis

Die Anwendung ist technisch vorbereitet, ersetzt aber noch keine abgestimmten Arbeitsanweisungen oder rechtlichen Vorgaben.
