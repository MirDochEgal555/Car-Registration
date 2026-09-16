# Extraktionsregeln

## Ziel

Natürliche Werkstattsprache wird in strukturierte Entwurfsdaten umgewandelt. Diese Regeln beschreiben die KI-Extraktion vor der Mechaniker- und Büroprüfung.

Grundregel:

> Nur Informationen extrahieren, die explizit gesagt oder eindeutig aus einer standardisierten Schreibweise normalisiert werden können.

Es werden keine Werte geraten.

## Ausführungsgrenze der Phase 7

`POST /api/v1/extractions` nimmt ein unverändertes `transcript` entgegen und
führt die gesamte Kette aus: OpenAI Strict Structured Output →
Normalisierung → deterministische Fachvalidierung → Mapping in den bestehenden
`RegistrationDraft` → bestehende Registrierungsvalidierung. Die Antwort ist
der vorhandene `ValidationResponse`; `field_status` und `review_required`
bleiben auch im zurückgegebenen Entwurf erhalten. Ein leerer Text wird mit
`422`, ein nicht verfügbarer KI-Anbieter mit `503` und eine nicht verarbeitbare
KI-Antwort mit `502` abgelehnt.

## Technische Normalisierung nach der KI-Extraktion

Die zentrale Schicht
`app.services.extraction_normalization.normalize_extraction_payload` läuft auf
der strukturierten KI-Antwort, bevor sie gegen das interne
`StructuredExtractionResult`-Modell geprüft oder in einen Entwurf übernommen
wird. Sie arbeitet ausschließlich deterministisch und nutzt keine externen
Fahrzeug-, Reifen- oder Herstellerdatenbanken.

- Nur Felder mit Status `valid` werden normalisiert. `missing`, `uncertain`
  und `invalid` bleiben unverändert; insbesondere kann kein fehlendes Feld
  dadurch `valid` werden.
- Nicht eindeutig normalisierbare Zahlen-, Reifenart- oder Positionswerte
  werden zu `uncertain` mit `null`. Ein nicht eindeutig strukturiertes
  Kennzeichen bleibt als `invalid` mit seinem ursprünglichen Text erhalten.
  In beiden Fällen wird `review_required` neu aus allen Feldstatus abgeleitet.
- Kennzeichen werden nur bei klar erkennbaren drei Bestandteilen zu
  `KREIS-BUCHSTABEN ZAHL` formatiert, etwa `cw ab123` zu `CW-AB 123`. Es findet
  keine Ortsnamen- oder Kennzeichenkorrektur statt.
- Kilometerstände werden aus Ziffern mit deutschen Tausendertrennzeichen und
  optionalem `km`/`Kilometer` zu `mileage_km: int`; Profiltiefen aus Ziffern
  mit Dezimalkomma/-punkt und optionalem `mm`/`Millimeter` zu
  `tread_depth_mm: float`.
- Reifengrößen werden vollständig als `Breite/Querschnitt RZoll` erkannt,
  etwa `225 45 17`, `225/45 R17` oder `225 durch 45 auf 17`. Intern bleiben
  sie unverändert als die drei vorhandenen numerischen Felder `width_mm`,
  `aspect_ratio` und `rim_diameter_inch` gespeichert. Die Schicht füllt dabei
  keine als fehlend markierte Komponente auf.
- Reifenarten werden auf `winter`, `summer`, `all_season` oder `unknown`
  abgebildet. Für Hersteller gilt ausschließlich die dokumentierte Aliasregel
  `Conti` → `Continental`; Modelltexte werden lediglich getrimmt und nie aus
  dem Hersteller abgeleitet oder mit ihm zusammengeführt.
- Eindeutige Ortsangaben wie `vorne links`, `Vorderachse rechts` oder
  `hinten` werden auf `front_left`, `front_right` bzw. `rear` abgebildet.
  `links` oder `rechts` ohne Achse bleiben unklar und werden nicht geraten.

## Ausgabe-Konventionen

Im finalen `RegistrationDraft` sind `tire_change` für ein Reifenwechselprotokoll und `tire_storage` für ein Reifeneinlagerungsprotokoll erlaubt. Der aktuelle Extraktionsendpunkt erhält nur ein Transkript und ergänzt keinen Protokolltyp; ein fehlender Typ bleibt deshalb `missing`. Die vorhandene Mechanikeroberfläche verwaltet ihre Auswahl weiterhin separat und ist noch nicht automatisch mit dem Extraktionsendpunkt verbunden.

Bei einem einzelnen beschriebenen Reifensatz können Reifenwerte flach im Extraktionsergebnis stehen. Werden mehrere Reifensätze erwähnt, verwendet die Extraktion immer `tire_sets`; jeder Eintrag enthält eine `role` und ein `tire_set`-Objekt. Bei der Speicherung werden diese Daten auf `TireSet` und `ServiceTireSet` aus dem [Datenmodell](DATA_MODEL.md) abgebildet. Die zulässigen Rollen hängen vom Protokolltyp ab: `installed` und `removed` bei `tire_change`, `stored` bei `tire_storage`.

Für ein Einlagerungsprotokoll enthält ein gespeicherter Reifensatz zusätzlich `tires` mit einem Eintrag je einzelnem Reifen. Diese Einträge enthalten Hersteller, Profil, Profiltiefe, DOT-Nummer, Gebrauchsspuren und Beschädigungen. Felgenangaben gehören zum umschließenden `tire_set`.

Für ein Reifenwechselprotokoll werden Winter- und Sommerräder als getrennte Einträge in `tire_sets` ausgegeben. Profiltiefen werden mit `tire_set_role: installed` oder `tire_set_role: removed` an den jeweiligen Satz gebunden. Sichtprüfungen verwenden ebenfalls diese Rolle, damit Befunde nicht zwischen Winter- und Sommerrädern vermischt werden.

```json
{
  "tire_inspections": [
    {
      "tire_set_role": "installed",
      "tread_front_mm": 6.5,
      "tread_rear_mm": 6
    }
  ],
  "visual_inspections": [
    {
      "tire_set_role": "removed",
      "component": "rim",
      "result": "not_ok",
      "position": "rear_right",
      "notes": "Kratzer"
    }
  ]
}
```

```json
{
  "tire_sets": [
    {
      "role": "stored",
      "tire_set": {
        "tire_type": "summer",
        "quantity": 4
      }
    }
  ]
}
```

Der Vorgangsstatus wird nicht im Extraktionsergebnis verwendet. Fehlende oder unsichere Felder sowie Plausibilitätsprobleme werden so gekennzeichnet:

```json
{
  "model": null,
  "field_status": {
    "model": "uncertain"
  },
  "review_required": true
}
```

Erlaubte Werte für einen Feldstatus:

```text
missing
uncertain
invalid
valid
```

`valid` kennzeichnet einen geprüften, plausiblen Wert. `invalid` kennzeichnet einen vorhandenen, aber fachlich oder plausibilitätsseitig unzulässigen Wert. `review_required` wird zentral berechnet und ist bei mindestens einem Status `uncertain` oder `invalid` immer `true`; `missing` und `valid` setzen ihn nicht. Nicht genannte optionale Felder können entfallen oder mit `null` und `field_status: missing` ausgegeben werden.

## Keine erfundenen Informationen

Input:

> „Vier Michelin Winterreifen.“

Erlaubt:

```json
{
  "manufacturer": "Michelin",
  "quantity": 4,
  "tire_type": "winter"
}
```

Nicht erlaubt:

```json
{
  "model": "Alpin 6"
}
```

## Kennzeichen

Gesprochen:

```text
CW AB 123
```

Ausgabe:

```text
CW-AB 123
```

Ortsnamen dürfen nur dann in Kennzeichenkürzel normalisiert werden, wenn die Zuordnung eindeutig ist.

## Fahrzeugdaten im Reifenwechselprotokoll

Die Erstzulassung wird ohne erfundenen Tag als Monat und Jahr gespeichert. Vmax wird in km/h ausgegeben. Für die Antriebsart gelten diese Werte:

| Gesprochen | Normalisiert |
| --- | --- |
| Elektro, Elektroauto | `propulsion_type: electric` |
| Hybrid, Plug-in-Hybrid | `propulsion_type: hybrid` |

Beispiel:

> „Elektroauto, EZ März 2024, Vmax 180.“

```json
{
  "propulsion_type": "electric",
  "first_registration_month": "2024-03",
  "max_speed_kmh": 180
}
```

Ohne Jahr oder Monat bleibt die Erstzulassung unvollständig und wird als `missing` oder `uncertain` markiert; es wird kein Tag ergänzt.

## Kilometerstand

Gesprochen:

```text
73400 Kilometer
73 Tausend 400
```

Ausgabe:

```json
{
  "mileage_km": 73400
}
```

Die interne Einheit ist immer Kilometer.

## Reifenart

| Gesprochen | Normalisiert |
| --- | --- |
| Winterreifen | `winter` |
| Sommerreifen | `summer` |
| Ganzjahresreifen | `all_season` |
| Allwetterreifen | `all_season` |

Bei „Reifen“ ohne weitere Angabe wird `tire_type` mit `unknown` ausgegeben.

## Reifengröße

Typische Sprache:

```text
205 55 16
```

Normalisierte Darstellung:

```text
205/55 R16
```

Strukturierte Ausgabe:

```json
{
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16
}
```

Weitere erlaubte Varianten:

```text
205 55 R16
205 durch 55 16
205 55 auf 16
205 slash 55 R 16
```

Die Größe wird nur extrahiert, wenn alle drei Werte ausreichend eindeutig sind.

## Felgenangaben für die Einlagerung

Die Felgengröße wird als `rim_diameter_inch` in Zoll gespeichert. Felgenausführung, Hersteller und Typ werden nur im Einlagerungsprotokoll ausgegeben, wenn sie explizit genannt sind.

| Gesprochen | Normalisiert |
| --- | --- |
| Alufelge, Alu | `rim_category: alloy` |
| Stahlfelge, Stahl | `rim_category: steel` |
| Originalfelge, Original | `rim_category: original` |

Beispiel:

> „17-Zoll-Alufelgen von Dezent, Typ TZ.“

```json
{
  "rim_diameter_inch": 17,
  "rim_category": "alloy",
  "rim_manufacturer": "Dezent",
  "rim_model": "TZ"
}
```

## Hersteller und Modell

Hersteller dürfen nur über eine definierte Alias-Liste normalisiert werden:

| Gesprochen | Normalisiert |
| --- | --- |
| Conti | Continental |
| Michelin | Michelin |
| Goodyear | Goodyear |
| Bridgestone | Bridgestone |
| Pirelli | Pirelli |
| Hankook | Hankook |

Modelle werden ausschließlich übernommen, wenn sie explizit genannt sind.

```text
Michelin Alpin 6 → manufacturer: Michelin, model: Alpin 6
Michelin Winterreifen → manufacturer: Michelin, model: null
```

Bei einer unverständlichen Modellbezeichnung bleibt `model` leer und erhält den Feldstatus `uncertain`. Eine freie Hersteller- oder Modellvermutung ist nicht erlaubt.

## Anzahl

Gesprochen:

```text
vier Reifen
```

Ausgabe:

```json
{
  "quantity": 4
}
```

Ohne explizite Anzahl darf kein Wert von vier angenommen werden.

## Profiltiefe

### Achswerte

Gesprochen:

```text
vorne sechs, hinten fünf
```

Wenn der Kontext eindeutig Profiltiefe betrifft:

```json
{
  "tread_front_mm": 6,
  "tread_rear_mm": 5
}
```

### Einzelradwerte

Gesprochen:

```text
vorne links sechs, vorne rechts sechseinhalb,
hinten links fünf, hinten rechts viereinhalb
```

Ausgabe:

```json
{
  "tread_front_left_mm": 6,
  "tread_front_right_mm": 6.5,
  "tread_rear_left_mm": 5,
  "tread_rear_right_mm": 4.5
}
```

Die interne Einheit ist immer Millimeter.

Für ein Einlagerungsprotokoll wird die Profiltiefe dem einzelnen Reifen zugeordnet. Das Profil bezeichnet dabei die ausdrücklich genannte Profil- oder Modellbezeichnung; es wird nicht aus dem Hersteller abgeleitet.

```json
{
  "position": "front_left",
  "manufacturer": "Michelin",
  "profile": "Alpin 6",
  "tread_depth_mm": 6.5,
  "dot": "2324",
  "wear_marks_present": true,
  "has_damage": true,
  "damage_notes": "Riss in der Seitenwand"
}
```

Bei einer ausdrücklich genannten Beschädigung wird `has_damage: true` ausgegeben und die Beschreibung unverändert in `damage_notes` übernommen. Ohne beschriebene Beschädigung bleibt `damage_notes` leer; eine Schadensbeschreibung darf nicht erfunden werden.

## Reifenzustand

Zustände und Positionen werden immer als Elemente von `conditions` ausgegeben:

| Gesprochen | Normalisiert |
| --- | --- |
| außen abgefahren | `outer_wear` |
| innen abgefahren | `inner_wear` |
| ungleichmäßig abgefahren | `uneven_wear` |
| rissig | `cracked` |
| beschädigt | `damaged` |
| Nagel oder Fremdkörper | `foreign_object` |
| Profil zu niedrig | `low_tread` |

Beispiel:

> „Hinten rechts außen abgefahren.“

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

Die erlaubten Werte entsprechen den Enums `condition` und `position` im Datenmodell.

## Notizen und Service

Nicht strukturierbare, aber relevante Aussagen werden als Notiz gespeichert.

> „Kunde möchte beim nächsten Mal neue Reifen.“

```json
{
  "notes": "Kunde möchte beim nächsten Mal neue Reifen."
}
```

Eine solche Notiz darf nicht als aktuelle Reifenbestückung interpretiert werden.

## Korrekturen innerhalb einer Aufnahme

Eine spätere explizite Aussage überschreibt eine frühere Aussage für dasselbe Feld.

> „Vorne sechs Millimeter – nee, sechseinhalb.“

```json
{
  "tread_front_mm": 6.5
}
```

## Mehrdeutige und unplausible Aussagen

Input:

> „Die Reifen sind fünf.“

Dies darf weder als Anzahl noch als Profiltiefe ausgelegt werden:

```json
{
  "field_status": {
    "notes": "uncertain"
  },
  "review_required": true
}
```

Nach der Extraktion erfolgen Plausibilitätsprüfungen, zum Beispiel für positive Mengen, nicht negative Kilometerstände und plausible Felgendurchmesser. Die Prüfung markiert Daten, verändert sie aber nicht automatisch.

```json
{
  "tread_front_mm": 65,
  "review_required": true
}
```

Der Wert darf nicht eigenständig auf `6.5` korrigiert werden.

Ein nicht leeres Transkript ohne irgendeine extrahierbare Information, etwa
„Äh, na ja, Dingens.“, erzeugt ebenfalls keine Werte. Das Backend markiert in
diesem Fall ausschließlich `notes` als `uncertain` und setzt damit
`review_required: true`. So bleibt der Prüfbedarf sichtbar, ohne einen
fachlichen Wert zu ergänzen.

## Deterministische Fachvalidierung (Phase 7)

Nach der Normalisierung prüft das Backend die Extraktion ohne LLM, externe
Fahrzeugdatenbank oder Herstellerdatenbank. Die Prüfung ergänzt keine fehlende
Information und stuft niemals ein bereits als `missing`, `uncertain` oder
`invalid` markiertes Feld zu `valid` hoch. `review_required` wird danach erneut
aus allen Feldstatus bestimmt.

| Bereich | Harte Regel (`invalid`) | Inhaltliche Unsicherheit (`uncertain`) |
| --- | --- | --- |
| Kennzeichen | Exakt `KREIS-BUCHSTABEN ZAHL`, z. B. `CW-AB 123` (Kreis 1–3 Buchstaben, danach 1–2 Buchstaben, 1–4 Ziffern und optionaler Schlussbuchstabe) | — |
| Kilometerstand | Ganze Zahl von 0 bis 2.000.000 km | — |
| Reifenart und Zustand | — | Der Wert `unknown`/`unbekannt` ist nicht fachlich bestätigt und wird zu `uncertain`; vorhandene Unsicherheit bleibt erhalten. |
| Reifengröße | Breite 125–405 mm in 5-mm-Schritten, Querschnitt 20–95 in 5er-Schritten, Felge 10–24 Zoll | Fehlende Größenbestandteile bleiben `missing`; sie werden nicht ergänzt. |
| Anzahl | Ganze Zahl von 1 bis 8 je Reifensatz; mehr einzeln gelistete Reifen als die angegebene Menge ist widersprüchlich | — |
| Profiltiefe | Endlicher Zahlenwert von 0,0 bis 15,0 mm | Fehlende Messwerte bleiben `missing`, niemals automatisch `valid`. Zwei unterschiedliche Messwerte für dieselbe Rolle und dieselbe Achse/Position werden `uncertain`. |
| Reifenposition | Ein einzelner Reifen benötigt eine konkrete Position: `front_left`, `front_right`, `rear_left` oder `rear_right`. Ein `not_ok`-Sichtbefund darf nicht nur `front`, `rear` oder `all` haben. | Doppelt vergebene konkrete Positionen im selben Reifensatz sind nicht auflösbar und werden `uncertain`. `unknown`/`unbekannt` wird nie als `valid` übernommen. |
| Hersteller und Modell | — | Hersteller und Modell bleiben getrennt. Ein fehlendes oder bereits unsicheres Modell wird nicht aus dem Hersteller abgeleitet; `unbekannt` bleibt `uncertain`. |

Format- und Bereichsfehler behalten ihren ausdrücklich gelieferten Wert mit
Status `invalid`, damit die Prüfung nachvollziehbar bleibt. Bei
Mehrdeutigkeiten entfernt die Validierung den nicht sicher zuordenbaren Wert
und setzt `uncertain`. Beide Status setzen `review_required: true`.

## Reifenwechselprotokoll

In einem Reifenwechselprotokoll bleibt bei mehreren Reifensätzen ihre Rolle erhalten.

> „Wechsel auf Winterreifen. Abgenommen werden vier Michelin Sommerreifen 225 45 17.“

```json
{
  "service_type": "tire_change",
  "tire_sets": [
    {
      "role": "installed",
      "tire_set": {
        "tire_type": "winter"
      }
    },
    {
      "role": "removed",
      "tire_set": {
        "manufacturer": "Michelin",
        "tire_type": "summer",
        "quantity": 4,
        "width_mm": 225,
        "aspect_ratio": 45,
        "rim_diameter_inch": 17
      }
    }
  ]
}
```

Die genannten Sommerreifen dürfen nicht als montierter Satz gespeichert werden. Fehlen Details zum montierten Satz, werden sie nicht ergänzt.

Zusätzlich werden die Wechselarbeiten und Prüfergebnisse in `tire_change_details` ausgegeben. Gezählt wird nur die ausdrücklich genannte Anzahl von Wucht- oder Waschvorgängen; beispielsweise darf aus „Wuchten Stahl“ nicht automatisch `2` abgeleitet werden. Der WHM-Modus sowie die Angaben zum nächsten KD und Ölservice werden unverändert gespeichert, weil hierfür keine allgemeine Normalisierungsregel definiert ist.

```json
{
  "tire_change_details": {
    "wheel_change_performed": true,
    "balancing_steel_count": 2,
    "balancing_alloy_count": 2,
    "machine_wash_count": 4,
    "manual_wash_count": 4,
    "whm_mode": "Komfort",
    "next_customer_service": "05/2027",
    "next_oil_service": "06/2027",
    "air_pressure_front_bar": 2.4,
    "air_pressure_rear_bar": 2.3,
    "wheel_lock_present": true,
    "wheel_bolt_configuration": "different",
    "hu_due_month": "2027-03",
    "suspension_visual_result": "ok",
    "brake_visual_result": "not_ok",
    "hub_cleaned": true,
    "rdks_type": "active",
    "rdks_programmed": true,
    "speed_limiter_set": true,
    "speed_limiter_sticker_applied": true,
    "wheel_bolt_torque_nm": 120,
    "whatsapp_contact_allowed": true
  },
  "brake_disc_measurements": [
    {
      "position": "front_right",
      "thickness_mm": 19.5
    }
  ]
}
```

Die Luftdruckwerte sind Mittelwerte in bar für Vorderachse (`air_pressure_front_bar`) und Hinterachse (`air_pressure_rear_bar`). Die HU-Fälligkeit wird ohne erfundenen Tag als Monat und Jahr gespeichert. Eine Bremsscheibendicke wird nur bei `brake_visual_result: not_ok` ausgegeben.

### Sichtprüfungen

Felgen- und Reifensichtprüfungen werden je Winter- oder Sommersatz erfasst. `ok` beschreibt eine i.O.-Prüfung, `not_ok` eine n.i.O.-Prüfung. Bei `not_ok` ist die konkrete Position erforderlich; eine vorhandene Beschreibung wird in `notes` übernommen.

```json
{
  "visual_inspections": [
    {
      "tire_set_role": "installed",
      "component": "rim",
      "result": "ok",
      "position": "all"
    },
    {
      "tire_set_role": "removed",
      "component": "tire",
      "result": "not_ok",
      "position": "rear_right",
      "notes": "außen beschädigt"
    }
  ]
}
```

Für Winter- und Sommerräder werden Reifengröße, LI, VI, Hersteller, Profilbezeichnung und DOT direkt im jeweiligen `tire_set` gespeichert. Profiltiefen werden ausschließlich über `tire_inspections` mit passender `tire_set_role` ausgegeben; Werte eines Satzes dürfen nicht in den anderen kopiert werden.

```json
{
  "role": "installed",
  "tire_set": {
    "tire_type": "winter",
    "width_mm": 205,
    "aspect_ratio": 55,
    "rim_diameter_inch": 16,
    "load_index": "91",
    "speed_index": "H",
    "manufacturer": "Continental",
    "model": "WinterContact TS 870",
    "dot": "2524"
  }
}
```

Kundenunterschrift und WhatsApp-Freigabe werden über eine eindeutige Eingabe in der Oberfläche erfasst. Sie dürfen nicht aus einer beiläufigen Sprachäußerung abgeleitet werden. RDKS-Typ (aktiv/passiv) und der Status „angelernt“ sowie Limiter und Limiter-Aufkleber werden jeweils getrennt erfasst.

## Reifeneinlagerungsprotokoll

Ein Einlagerungsprotokoll enthält ausschließlich die einzulagernden Reifensätze. Kunde, Datum, Fahrzeug, Kennzeichen und Mechaniker stammen aus den zugehörigen Stammdaten beziehungsweise dem Vorgang; eine Kundenunterschrift wird über die Oberfläche erfasst und niemals aus Sprache erzeugt.

> „Eingelagert werden vier Michelin Sommerreifen auf 17-Zoll-Alufelgen von Dezent, Typ TZ. Vorne links: Alpin 6, Profil sechs Komma fünf, DOT 2324, Gebrauchsspuren ja, Riss in der Seitenwand.“

```json
{
  "service_type": "tire_storage",
  "tire_sets": [
    {
      "role": "stored",
      "tire_set": {
        "tire_type": "summer",
        "quantity": 4,
        "rim_diameter_inch": 17,
        "rim_category": "alloy",
        "rim_manufacturer": "Dezent",
        "rim_model": "TZ",
        "tires": [
          {
            "position": "front_left",
            "manufacturer": "Michelin",
            "profile": "Alpin 6",
            "tread_depth_mm": 6.5,
            "dot": "2324",
            "wear_marks_present": true,
            "has_damage": true,
            "damage_notes": "Riss in der Seitenwand"
          }
        ]
      }
    }
  ]
}
```

Die Angaben unter `tires` werden für jeden genannten Reifen einzeln ausgegeben. Eine nicht genannte DOT-Nummer, Profiltiefe, Gebrauchsspur oder Beschädigung bleibt leer oder als `missing` markiert; sie darf nicht vom Rest des Satzes kopiert werden. Ein genannter montierter oder demontierter Satz wird nicht in ein Einlagerungsprotokoll übernommen. Ein Reifenwechsel wird immer über ein separates Reifenwechselprotokoll dokumentiert.

## Priorität der Datenquellen

Bei widersprüchlichen Angaben für dasselbe Feld gilt diese Reihenfolge:

```text
Bürokorrektur
> Mechanikerkorrektur
> durch Mechaniker bestätigter KI-Wert
> KI-Extraktion
```

Das Originaltranskript bleibt im finalen Entwurf erhalten. Die API liefert den
normalisierten und validierten Entwurf samt Feldstatus; eine separate rohe
KI-Antwort wird im MVP nicht zusätzlich persistiert. Nach Mechanikerbestätigung
wird das unveränderte Rohtranskript zusammen mit dem finalen Entwurf in der
Versand-Outbox aufbewahrt und nicht in die E-Mail gerendert.
