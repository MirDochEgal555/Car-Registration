# Services

`registrationApi.ts` kapselt alle FastAPI-Aufrufe für Validierung, Versand,
Status und Retry. `registrationMapper.ts` übersetzt das lokale camelCase-
Formularmodell in den snake_case-`RegistrationDraft`-Vertrag des Backends.

`audioApi.ts` liefert weiterhin ausschließlich das unveränderte Transkript.
Die neue Backend-Route `POST /api/v1/extractions` ist absichtlich noch nicht
in den Frontend-Services verdrahtet; die spätere Anbindung muss ihren
`ValidationResponse` als prüfbaren Entwurf behandeln und darf manuelle Werte
nicht stillschweigend überschreiben.
