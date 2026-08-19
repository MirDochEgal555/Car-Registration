# Extraktionsregeln

## Ziel

Natürliche Werkstattsprache wird in strukturierte Entwurfsdaten umgewandelt. Diese Regeln beschreiben die KI-Extraktion vor der Mechaniker- und Büroprüfung.

Grundregel:

> Nur Informationen extrahieren, die explizit gesagt oder eindeutig aus einer standardisierten Schreibweise normalisiert werden können.

Es werden keine Werte geraten.

## Ausgabe-Konventionen

Bei einem einzelnen beschriebenen Reifensatz können Reifenwerte flach im Extraktionsergebnis stehen. Werden mehrere Reifensätze erwähnt, verwendet die Extraktion immer `tire_sets`; jeder Eintrag enthält eine `role` und ein `tire_set`-Objekt. Bei der Speicherung werden diese Daten auf `TireSet` und `ServiceTireSet` aus dem [Datenmodell](DATA_MODEL.md) abgebildet.

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
```

`review_required` muss bei unsicheren oder unplausiblen Angaben `true` sein. Nicht genannte optionale Felder können entfallen oder mit `null` und `field_status: missing` ausgegeben werden.

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
    "statement": "uncertain"
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

## Saisonaler Reifenwechsel

Bei mehreren Reifensätzen bleibt ihre Rolle erhalten.

> „Wechsel auf Winterreifen. Eingelagert werden vier Michelin Sommerreifen 225 45 17.“

```json
{
  "service_type": "seasonal_tire_change",
  "tire_sets": [
    {
      "role": "installed",
      "tire_set": {
        "tire_type": "winter"
      }
    },
    {
      "role": "stored",
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

## Priorität der Datenquellen

Bei widersprüchlichen Angaben für dasselbe Feld gilt diese Reihenfolge:

```text
Bürokorrektur
> Mechanikerkorrektur
> durch Mechaniker bestätigter KI-Wert
> KI-Extraktion
```

Das Originaltranskript und die ursprüngliche KI-Ausgabe bleiben für Audit-Zwecke erhalten.
