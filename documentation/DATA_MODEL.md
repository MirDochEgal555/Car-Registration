# Datenmodell

## Ziel

Das Datenmodell bildet Fahrzeugaufnahmen und saisonale Reifenwechsel ab. Es trennt KI-Rohdaten, geprüfte Fachwerte und Verwaltungsdaten, damit jede Korrektur nachvollziehbar bleibt.

Wichtige Prinzipien:

- Informationen werden strukturiert gespeichert.
- Fehlende oder unsichere Informationen werden nicht geraten.
- Die Kundenanlage und -zuordnung erfolgt im Büro, nicht durch den Mechaniker.
- KI-Extraktion und final geprüfte Daten bleiben unterscheidbar.
- Eine spätere WERBAS-Integration bleibt möglich.

## Beziehungen

```text
Customer
└── Vehicle (customer_id optional)
    └── ServiceRecord
        ├── TireInspection
        │   └── TireCondition
        └── ServiceTireSet
            └── TireSet
```

Ein `Vehicle` kann vor der Büroprüfung ohne `customer_id` angelegt werden. Ein `ServiceRecord` kann mehrere Reifensätze referenzieren; ihre Rolle ist immer explizit.

## Customer (Kunde)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| first_name | string | nein | Vorname |
| last_name | string | nein | Nachname |
| phone | string | nein | Telefonnummer |
| email | string | nein | E-Mail-Adresse |
| notes | text | nein | allgemeine Hinweise |
| created_at | datetime | ja | Erstellungszeitpunkt |
| updated_at | datetime | ja | letzter Änderungszeitpunkt |
| werbas_customer_id | string | nein | spätere WERBAS-Zuordnung |

## Vehicle (Fahrzeug)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| customer_id | UUID | nein | zugehöriger Kunde |
| license_plate | string | ja | normalisiertes Kennzeichen |
| mileage_km | integer | nein | aktueller Kilometerstand |
| make | string | nein | Hersteller |
| model | string | nein | Fahrzeugmodell |
| vin | string | nein | Fahrgestellnummer |
| created_at | datetime | ja | Erstellungszeitpunkt |
| updated_at | datetime | ja | letzter Änderungszeitpunkt |
| werbas_vehicle_id | string | nein | spätere WERBAS-Zuordnung |

Beispiel:

```json
{
  "license_plate": "CW-AB 123",
  "mileage_km": 73400
}
```

## ServiceRecord (Servicevorgang)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| vehicle_id | UUID | ja | Fahrzeug |
| service_type | enum | ja | Vorgangstyp |
| status | enum | ja | Ablaufstatus |
| notes | text | nein | allgemeine Servicehinweise |
| raw_transcript | text | nein | originales Sprachtranskript |
| extraction_payload | JSONB | nein | unveränderte KI-Extraktion |
| field_status | JSONB | nein | Status einzelner extrahierter Felder |
| review_required | boolean | ja | Prüfung wegen Unsicherheit oder Validierung nötig |
| created_by | UUID | nein | Mechaniker |
| mechanic_confirmed_at | datetime | nein | Bestätigung durch Mechaniker |
| office_reviewed_at | datetime | nein | Prüfung durch Büro |
| created_at | datetime | ja | Erstellungszeitpunkt |
| updated_at | datetime | ja | letzter Änderungszeitpunkt |
| werbas_order_id | string | nein | spätere WERBAS-Zuordnung |

### service_type

```text
seasonal_tire_change
new_customer_registration
```

### status

```text
draft
mechanic_review
office_review
completed
rejected
```

`status` beschreibt ausschließlich den Lebenszyklus eines Vorgangs. `field_status` enthält beispielsweise `missing` oder `uncertain`; `review_required` markiert einen offenen Prüfbedarf.

## TireSet (Reifensatz)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| tire_type | enum | nein | Sommer, Winter oder Ganzjahr |
| width_mm | integer | nein | z. B. 205 |
| aspect_ratio | integer | nein | z. B. 55 |
| rim_diameter_inch | integer | nein | z. B. 16 |
| manufacturer | string | nein | Hersteller |
| model | string | nein | Reifenmodell |
| quantity | integer | nein | Anzahl Reifen |
| dot | string | nein | DOT-Angabe |
| notes | text | nein | Hinweise |

### tire_type

```text
summer
winter
all_season
unknown
```

Eine Reifengröße wird strukturiert gespeichert:

```json
{
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16
}
```

Für die Oberfläche wird sie als `205/55 R16` formatiert.

## ServiceTireSet (Reifensatz im Vorgang)

Diese Zuordnung verbindet einen Reifensatz mit einem Servicevorgang und hält seine Rolle fest.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| service_record_id | UUID | ja | Servicevorgang |
| tire_set_id | UUID | ja | Reifensatz |
| role | enum | ja | Rolle des Satzes im Vorgang |

### role

```text
installed
removed
stored
```

Bei „eingelagert“ wird `stored` verwendet; bei ausschließlich genannter Demontage `removed`. Ein montierter Satz erhält `installed`. Dieselbe physische Reifenmenge kann bei Bedarf sowohl als `removed` als auch als `stored` zugeordnet werden.

## TireInspection (Reifenprüfung)

Die Reifenprüfung beschreibt Profiltiefe und allgemeine Hinweise zum Zeitpunkt des Servicevorgangs.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| service_record_id | UUID | ja | Servicevorgang |
| service_tire_set_id | UUID | nein | geprüfter Reifensatz im Vorgang |
| tread_front_left_mm | decimal | nein | Profil vorne links |
| tread_front_right_mm | decimal | nein | Profil vorne rechts |
| tread_rear_left_mm | decimal | nein | Profil hinten links |
| tread_rear_right_mm | decimal | nein | Profil hinten rechts |
| tread_front_mm | decimal | nein | vereinfachter Vorderachsenwert |
| tread_rear_mm | decimal | nein | vereinfachter Hinterachsenwert |
| notes | text | nein | zusätzliche Hinweise |

Wenn nur „vorne 6, hinten 5“ genannt wird, werden Achswerte gespeichert und Einzelradwerte bleiben leer:

```json
{
  "tread_front_mm": 6,
  "tread_rear_mm": 5
}
```

## TireCondition (Reifenzustand)

Jeder erkannte Zustand wird als eigener Datensatz gespeichert. Dadurch können mehrere Zustände und Positionen ohne Bedeutungsverlust abgebildet werden.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| tire_inspection_id | UUID | ja | zugehörige Reifenprüfung |
| condition | enum | ja | erkannter Zustand |
| position | enum | ja | zugehörige Position |
| notes | text | nein | zusätzliche Erläuterung |

### condition

```text
ok
worn
uneven_wear
inner_wear
outer_wear
damaged
cracked
foreign_object
low_tread
unknown
```

### position

```text
front_left
front_right
rear_left
rear_right
front
rear
unknown
```

Beispiel für ein Extraktionsergebnis:

```json
{
  "conditions": [
    {
      "condition": "outer_wear",
      "position": "rear_right"
    }
  ]
}
```
