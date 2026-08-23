# Datenmodell

## Ziel

Das Datenmodell beschreibt die strukturierte Ausgabe für die beiden Werkstattprotokolle Reifenwechsel und Reifeneinlagerung. Im MVP wird diese Struktur als E-Mail-Text an das Büro übergeben; die dauerhafte Speicherung und finale Bearbeitung erfolgen in WERBAS. Das Modell dient zugleich als saubere Grundlage für eine optionale spätere zentrale Speicherung.

Wichtige Prinzipien:

- Informationen werden für E-Mail und spätere Speicheroptionen strukturiert aufbereitet.
- Fehlende oder unsichere Informationen werden nicht geraten.
- Die Kundenanlage und -zuordnung erfolgt durch das Büro in WERBAS, nicht durch den Mechaniker.
- KI-Extraktion und Prüfhinweise bleiben in der strukturierten E-Mail unterscheidbar.
- Eine zentrale Speicherung und Büro-Oberfläche bleiben optionale Erweiterungen. Für die technische Zustellung hält der MVP jedoch eine kleine, lokale Versand-Outbox vor, damit bestätigte Datensätze bei SMTP-Fehlern nicht verloren gehen.
- Eine direkte technische WERBAS-Integration ist nicht Teil des MVP.

## Optionales Zieldatenmodell

Die folgenden Beziehungen beschreiben eine mögliche spätere zentrale Speicherung. Sie werden im MVP nicht als CarTech-Datenbank implementiert; WERBAS ist das führende Speichersystem.

```text
Customer
└── Vehicle (customer_id optional)
    └── ServiceRecord
        ├── CustomerSignature
        ├── TireChangeDetails (nur bei tire_change)
        │   └── BrakeDiscMeasurement
        ├── TireInspection
        │   └── TireCondition
        ├── VisualInspection
        └── ServiceTireSet
            └── TireSet
                └── Tire
```

Ein `Vehicle` kann im optionalen Zieldatenmodell vor der Büroprüfung ohne `customer_id` angelegt werden. Ein `ServiceRecord` kann mehrere Reifensätze referenzieren; ihre Rolle ist immer explizit.

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
| propulsion_type | enum | nein | Antriebsart: Elektro, Hybrid oder andere |
| first_registration_month | year_month | nein | Erstzulassung (EZ), Monat und Jahr |
| max_speed_kmh | integer | nein | Höchstgeschwindigkeit (Vmax) |
| vin | string | nein | Fahrgestellnummer |
| created_at | datetime | ja | Erstellungszeitpunkt |
| updated_at | datetime | ja | letzter Änderungszeitpunkt |
| werbas_vehicle_id | string | nein | spätere WERBAS-Zuordnung |

Beispiel:

```json
{
  "license_plate": "CW-AB 123",
  "mileage_km": 73400,
  "propulsion_type": "electric",
  "first_registration_month": "2024-03",
  "max_speed_kmh": 180
}
```

### propulsion_type

```text
electric
hybrid
other
unknown
```

## ServiceRecord (Servicevorgang)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| vehicle_id | UUID | ja | Fahrzeug |
| service_type | enum | ja | Protokolltyp |
| service_date | date | ja | Datum des Werkstattprotokolls |
| status | enum | ja | Ablaufstatus |
| notes | text | nein | allgemeine Servicehinweise |
| raw_transcript | text | nein | originales Sprachtranskript |
| extraction_payload | JSONB | nein | unveränderte KI-Extraktion |
| field_status | JSONB | nein | Status einzelner extrahierter Felder |
| review_required | boolean | ja | Prüfung wegen Unsicherheit oder Validierung nötig |
| created_by | UUID | ja | erfassender Mechaniker |
| mechanic_confirmed_at | datetime | nein | Bestätigung durch Mechaniker |
| submitted_at | datetime | nein | erfolgreicher Versandzeitpunkt der strukturierten E-Mail |
| office_reviewed_at | datetime | nein | Prüfung durch Büro |
| created_at | datetime | ja | Erstellungszeitpunkt |
| updated_at | datetime | ja | letzter Änderungszeitpunkt |
| werbas_order_id | string | nein | spätere WERBAS-Zuordnung |

### service_type

```text
tire_change
tire_storage
```

`tire_change` steht für ein Reifenwechselprotokoll, `tire_storage` für ein Reifeneinlagerungsprotokoll. Die Kundenanlage oder -zuordnung erfolgt nicht über einen eigenen `service_type`, sondern im Büro.

### status

```text
draft
mechanic_review
email_pending
email_sending
email_sent
email_failed
new
in_review
completed
rejected
```

`status` gehört zum optionalen Zieldatenmodell. Für die MVP-Zustellung wird der bestätigte Datensatz vor dem SMTP-Aufruf lokal als `email_pending` abgelegt und während des laufenden Versuchs als `email_sending` geführt. Nimmt der Mailserver die Nachricht an, wird der Status `email_sent`; bei Konfigurations-, Verbindungs- oder Zustellfehlern `email_failed`. Ein fehlgeschlagener Datensatz bleibt zusammen mit Versuchszähler und einer sicheren Fehlermeldung in der Versand-Outbox erhalten und kann erneut versendet werden. Nach erfolgreicher Zustellung endet die fachliche weitere Statusführung in WERBAS. Bei einer späteren zentralen Büro-Oberfläche können zusätzlich die Status `new`, `in_review` und `completed` verwendet werden.

`field_status` enthält für jedes gekennzeichnete Feld einen der Werte `missing`, `uncertain`, `invalid` oder `valid`. `review_required` wird zentral aus diesen Feldstatus berechnet: Er ist genau dann `true`, wenn mindestens ein Feld `uncertain` oder `invalid` ist. `missing` (bei optionalen Angaben) und `valid` lösen allein keinen Prüfbedarf aus. Im MVP werden diese Markierungen in den E-Mail-Abschnitt „Prüfhinweise“ übernommen. In einer späteren Büro-Oberfläche müssen sie direkt am jeweiligen Feld angezeigt werden.

Bei `tire_storage` und `tire_change` müssen für die Übernahme in WERBAS mindestens ein Fahrzeug mit Kennzeichen, das Protokolldatum und der Mechaniker vorhanden sein. Kundenanlage oder -zuordnung bleibt Aufgabe des Büros.

## MVP-E-Mail-Ausgabe

Nach der Mechanikerbestätigung rendert das System den strukturierten Entwurf für die konfigurierte Büro-Adresse als `multipart/alternative`-E-Mail. Eine HTML- und eine Textansicht entstehen aus demselben E-Mail-Dokument und enthalten daher identische Fachinformationen: Protokolltyp, Kennzeichen, Absendezeitpunkt, alle erfassten Fahrzeug-, Reifen- und Servicedaten sowie einen getrennten Abschnitt „Prüfhinweise“ für `missing`, `uncertain` und `invalid`. Die Textansicht bleibt für reine Text-Mailclients und Weiterleitungen verfügbar.

Die E-Mail ersetzt im MVP weder WERBAS noch eine zentrale CarTech-Datenbank. Damit ein SMTP-Fehler keinen bestätigten Vorgang still verliert, wird die vollständige, validierte Fassung der strukturierten Protokolldaten vor dem Versand in einer lokalen SQLite-Versand-Outbox gespeichert; das Rohtranskript wird dabei nicht übernommen. `GET /api/v1/registrations/{id}/delivery-status` zeigt Status, Fehler und Versuchszähler; `POST /api/v1/registrations/{id}/retry` versendet den gespeicherten Datensatz erneut. Die Outbox enthält personenbezogene Werkstattdaten und muss deshalb im Produktivbetrieb auf einem persistenten, zugriffsgeschützten und verschlüsselten Volume liegen.

## CustomerSignature (Kundenunterschrift)

Diese Erweiterung existiert höchstens einmal je `ServiceRecord` und steht für die Kundenunterschrift in beiden Protokollen zur Verfügung.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| service_record_id | UUID | ja | zugehöriges Werkstattprotokoll |
| customer_signature | binary | ja | erfasste Unterschrift des Kunden |
| customer_signed_at | datetime | ja | Zeitpunkt der Unterschrift |

Die Unterschrift ist als geschützter Binärwert beziehungsweise als Verweis auf einen geschützten Dateispeicher abzulegen; sie wird nicht im Sprachtranskript gespeichert.

## TireChangeDetails (Wechseldetails)

Diese Erweiterung existiert genau einmal für einen `ServiceRecord` mit `service_type: tire_change`. Kunde, Datum, Fahrzeug, Kennzeichen und Kilometerstand werden über `Customer`, `Vehicle` und `ServiceRecord` geführt; die folgenden Angaben gehören ausschließlich zum Reifenwechselprotokoll.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| service_record_id | UUID | ja | zugehöriges Reifenwechselprotokoll |
| wheel_change_performed | boolean | ja | RäWe durchgeführt: Ja oder Nein |
| balancing_steel_count | integer | nein | Anzahl gewuchteter Stahlräder, z. B. 2 |
| balancing_alloy_count | integer | nein | Anzahl gewuchteter Aluräder, z. B. 2 |
| machine_wash_count | integer | nein | Anzahl maschinell gewaschener Räder, z. B. 4 |
| manual_wash_count | integer | nein | Anzahl manuell gewaschener Räder, z. B. 4 |
| whm_mode | string | nein | ausgewählter WHM-Modus ohne Umdeutung |
| next_customer_service | string | nein | Angabe zum nächsten Kundendienst (KD) |
| next_oil_service | string | nein | Angabe zum nächsten Ölservice |
| air_pressure_front_bar | decimal | nein | Luftdruck-Mittelwert Vorderachse in bar |
| air_pressure_rear_bar | decimal | nein | Luftdruck-Mittelwert Hinterachse in bar |
| wheel_lock_present | boolean | nein | Felgenschloss vorhanden: Ja oder Nein |
| wheel_bolt_configuration | enum | nein | gleiche oder verschiedene Radschrauben |
| hu_due_month | year_month | nein | Fälligkeit der Hauptuntersuchung (HU), Monat und Jahr |
| suspension_visual_result | enum | nein | Fahrwerksichtprüfung: i.O. oder n.i.O. |
| brake_visual_result | enum | nein | Bremsensichtprüfung: i.O. oder n.i.O. |
| hub_cleaned | boolean | nein | Radnabe gereinigt: Ja oder Nein |
| rdks_type | enum | nein | RDKS aktiv oder passiv |
| rdks_programmed | boolean | nein | RDKS angelernt: Ja oder Nein |
| speed_limiter_set | boolean | nein | Limiter gesetzt: Ja oder Nein |
| speed_limiter_sticker_applied | boolean | nein | Limiter-Aufkleber angebracht: Ja oder Nein |
| wheel_bolt_torque_nm | decimal | nein | Drehmoment der Radschrauben in Nm |
| whatsapp_contact_allowed | boolean | nein | WhatsApp-Kontakt erlaubt: Ja oder Nein |

### wheel_bolt_configuration

```text
same
different
unknown
```

### Sichtprüfungs-Ergebnis

```text
ok
not_ok
unknown
```

`rdks_type` und `rdks_programmed` sind getrennte Felder: Ein RDKS kann aktiv oder passiv sein und zusätzlich angelernt werden. Gleiches gilt für `speed_limiter_set` und den Limiter-Aufkleber; beide Angaben werden getrennt dokumentiert.

## BrakeDiscMeasurement (Bremsscheibendicke)

Eine Bremsscheibendicke wird nur erfasst, wenn die Bremsensichtprüfung `not_ok` ist.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| tire_change_details_id | UUID | ja | zugehörige Wechseldetails |
| position | enum | ja | Position der gemessenen Bremsscheibe |
| thickness_mm | decimal | ja | Bremsscheibendicke in Millimetern |

## TireSet (Reifensatz)

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| tire_type | enum | nein | Sommer, Winter oder Ganzjahr |
| width_mm | integer | nein | z. B. 205 |
| aspect_ratio | integer | nein | z. B. 55 |
| rim_diameter_inch | integer | nein | Felgengröße in Zoll, z. B. 16 |
| rim_category | enum | nein | Alu, Stahl oder Original |
| rim_manufacturer | string | nein | Felgenhersteller |
| rim_model | string | nein | Felgentyp oder -modell |
| manufacturer | string | nein | Hersteller |
| model | string | nein | Profilbezeichnung beziehungsweise Reifenmodell |
| quantity | integer | nein | Anzahl Reifen |
| dot | string | nein | DOT-Angabe |
| load_index | string | nein | Tragfähigkeitsindex (LI), z. B. 91 |
| speed_index | string | nein | Geschwindigkeitsindex (VI), z. B. H |
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

### rim_category

```text
alloy
steel
original
unknown
```

`alloy`, `steel` und `original` entsprechen den Auswahlwerten Alu, Stahl und Original im Einlagerungsprotokoll. Für ein `tire_storage`-Protokoll werden Felgengröße, Felgenausführung, Felgenhersteller und Felgentyp am Reifensatz erfasst.

## Tire (Einzelreifen)

Ein `Tire` gehört zu genau einem `TireSet`. Für ein Einlagerungsprotokoll sind diese Werte je einzelnem Reifen zu erfassen; damit können unterschiedliche Profiltiefen, DOT-Nummern und Schäden innerhalb eines Satzes abgebildet werden.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| tire_set_id | UUID | ja | zugehöriger Reifensatz |
| position | enum | ja | Position am Fahrzeug oder eindeutige Reihenfolge |
| manufacturer | string | nein | Reifenhersteller des einzelnen Reifens |
| profile | string | nein | Reifenprofil beziehungsweise Modellbezeichnung |
| tread_depth_mm | decimal | nein | gemessene Profiltiefe in Millimetern |
| dot | string | nein | DOT-Nummer |
| wear_marks_present | boolean | ja | Gebrauchsspuren vorhanden: Ja oder Nein |
| has_damage | boolean | ja | Beschädigung vorhanden: Ja oder Nein |
| damage_notes | text | nein | Beschreibung der Beschädigung |

`manufacturer`, `model` und `dot` auf `TireSet` bleiben für allgemeine Reifenwechsel- und Altdaten erhalten. Bei einer Einlagerung sind die Werte des jeweiligen `Tire` maßgeblich.

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

| Protokolltyp | Erlaubte Rollen | Bedeutung |
| --- | --- | --- |
| `tire_change` | `installed`, `removed` | montierter beziehungsweise demontierter Satz |
| `tire_storage` | `stored` | einzulagernder Satz |

Bei einem Reifenwechsel wird ein montierter Satz als `installed` und ein demontierter Satz als `removed` gespeichert. Bei einer Einlagerung wird ausschließlich `stored` verwendet. Soll ein demontierter Satz eingelagert werden, wird dafür zusätzlich ein separates Reifeneinlagerungsprotokoll erstellt.

Im Reifenwechselprotokoll werden Winter- und Sommerräder jeweils als eigener `ServiceTireSet` gespeichert. Reifengröße, LI, VI, Hersteller, Profilbezeichnung und DOT-Angabe gehören zum jeweiligen `TireSet`; Profiltiefen und Sichtprüfungen werden über dessen Zuordnung zum Vorgang erfasst.

## TireInspection (Reifenprüfung)

Die Reifenprüfung beschreibt Profiltiefe und allgemeine Hinweise zum Zeitpunkt eines Reifenwechselprotokolls. Für das Einlagerungsprotokoll wird die Profiltiefe je Reifen in `Tire.tread_depth_mm` gespeichert.

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

## VisualInspection (Felgen- und Reifensichtprüfung)

Eine Sichtprüfung dokumentiert Felge oder Reifen eines Reifensatzes im Reifenwechselprotokoll. Sie kann für alle Positionen oder für eine konkrete auffällige Position angelegt werden.

| Feld | Typ | Pflicht | Beschreibung |
| --- | --- | :---: | --- |
| id | UUID | ja | interne ID |
| service_record_id | UUID | ja | Reifenwechselprotokoll |
| service_tire_set_id | UUID | ja | geprüfter Winter- oder Sommersatz |
| component | enum | ja | `rim` oder `tire` |
| result | enum | ja | `ok` oder `not_ok` |
| position | enum | ja | geprüfte oder auffällige Radposition |
| notes | text | nein | Beschreibung, zum Beispiel Kratzer |

Für eine i.O.-Prüfung aller Räder wird `position: all` verwendet. Für eine n.i.O.-Prüfung ist die konkrete Position Pflicht.

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
all
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
