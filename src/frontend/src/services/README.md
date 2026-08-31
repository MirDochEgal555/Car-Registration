# Services

`registrationApi.ts` kapselt alle FastAPI-Aufrufe für Validierung, Versand,
Status und Retry. `registrationMapper.ts` übersetzt das lokale camelCase-
Formularmodell in den snake_case-`RegistrationDraft`-Vertrag des Backends.
