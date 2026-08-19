# Extraktions-Testfälle

## Ziel

Diese Tests prüfen, ob Spracheingaben zuverlässig in die erwartete Struktur überführt werden. Sie verwenden die in den [Extraktionsregeln](EXTRACTION_RULES.md) definierte Ausgabeform.

Nicht genannte optionale Felder bleiben nicht gesetzt oder erhalten den Wert `null` mit `field_status: missing`. Unsichere oder unplausible Angaben setzen `review_required` auf `true`.

## Test 01 – Standardfall

### Eingabe

> „CW AB 123, 73400 Kilometer, vier Michelin Alpin 6 Winterreifen, 205 55 16, vorne sechs Millimeter, hinten fünf.“

### Erwartete Ausgabe

```json
{
  "license_plate": "CW-AB 123",
  "mileage_km": 73400,
  "tire_type": "winter",
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16,
  "manufacturer": "Michelin",
  "model": "Alpin 6",
  "quantity": 4,
  "tread_front_mm": 6,
  "tread_rear_mm": 5
}
```

## Test 02 – Andere Reihenfolge

### Eingabe

> „Vier Winterreifen von Continental, 205 55 R16. Kennzeichen CW XY 42. 82 Tausend Kilometer.“

### Erwartete Ausgabe

```json
{
  "license_plate": "CW-XY 42",
  "mileage_km": 82000,
  "tire_type": "winter",
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16,
  "manufacturer": "Continental",
  "quantity": 4,
  "model": null,
  "field_status": {
    "model": "missing"
  }
}
```

## Test 03 – Herstelleralias

### Eingabe

> „Vier Conti Winterreifen.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Continental",
  "tire_type": "winter",
  "quantity": 4
}
```

## Test 04 – Modell darf nicht geraten werden

### Eingabe

> „Michelin Winterreifen, vier Stück.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Michelin",
  "tire_type": "winter",
  "quantity": 4,
  "model": null,
  "field_status": {
    "model": "missing"
  }
}
```

## Test 05 – Profiltiefe je Achse

### Eingabe

> „Profil vorne sechseinhalb, hinten fünfeinhalb.“

### Erwartete Ausgabe

```json
{
  "tread_front_mm": 6.5,
  "tread_rear_mm": 5.5
}
```

## Test 06 – Einzelradwerte

### Eingabe

> „Vorne links sieben, vorne rechts sechseinhalb, hinten links fünf und hinten rechts viereinhalb Millimeter.“

### Erwartete Ausgabe

```json
{
  "tread_front_left_mm": 7,
  "tread_front_right_mm": 6.5,
  "tread_rear_left_mm": 5,
  "tread_rear_right_mm": 4.5
}
```

## Test 07 – Reifenverschleiß

### Eingabe

> „Hinten rechts ist der Reifen außen abgefahren.“

### Erwartete Ausgabe

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

## Test 08 – Mehrere Zustände

### Eingabe

> „Vorne links ist der Reifen rissig und hinten rechts ungleichmäßig abgefahren.“

### Erwartete Ausgabe

```json
{
  "conditions": [
    {
      "condition": "cracked",
      "position": "front_left"
    },
    {
      "condition": "uneven_wear",
      "position": "rear_right"
    }
  ]
}
```

## Test 09 – Korrektur während Spracheingabe

### Eingabe

> „Kilometerstand 82.300, nee 82.350.“

### Erwartete Ausgabe

```json
{
  "mileage_km": 82350
}
```

## Test 10 – Profiltiefe korrigiert

### Eingabe

> „Vorne sechs Millimeter, nee sechseinhalb, hinten fünf.“

### Erwartete Ausgabe

```json
{
  "tread_front_mm": 6.5,
  "tread_rear_mm": 5
}
```

## Test 11 – Reifengröße umgangssprachlich

### Eingabe

> „205 durch 55 auf 16.“

### Erwartete Ausgabe

```json
{
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16
}
```

## Test 12 – Reifengröße mit R

### Eingabe

> „225 45 R 17.“

### Erwartete Ausgabe

```json
{
  "width_mm": 225,
  "aspect_ratio": 45,
  "rim_diameter_inch": 17
}
```

## Test 13 – Ganzjahresreifen

### Eingabe

> „Vier Goodyear Allwetterreifen.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Goodyear",
  "tire_type": "all_season",
  "quantity": 4
}
```

## Test 14 – Keine Reifenart angegeben

### Eingabe

> „Vier Hankook Reifen, 205 55 16.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Hankook",
  "quantity": 4,
  "width_mm": 205,
  "aspect_ratio": 55,
  "rim_diameter_inch": 16,
  "tire_type": "unknown"
}
```

## Test 15 – Anzahl fehlt

### Eingabe

> „Michelin Alpin 6 Winterreifen.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Michelin",
  "model": "Alpin 6",
  "tire_type": "winter",
  "quantity": null,
  "field_status": {
    "quantity": "missing"
  }
}
```

Ein Wert von vier darf nicht angenommen werden.

## Test 16 – Mehrdeutige Aussage

### Eingabe

> „Die Reifen sind fünf.“

### Erwartete Ausgabe

```json
{
  "field_status": {
    "statement": "uncertain"
  },
  "review_required": true
}
```

## Test 17 – Unrealistischer Wert

### Eingabe

> „Vorne 65 Millimeter Profil.“

### Erwartete Ausgabe

```json
{
  "tread_front_mm": 65,
  "review_required": true
}
```

Der Wert darf nicht automatisch auf `6.5` geändert werden.

## Test 18 – Notiz

### Eingabe

> „Kunde möchte im Frühjahr vier neue Sommerreifen.“

### Erwartete Ausgabe

```json
{
  "notes": "Kunde möchte im Frühjahr vier neue Sommerreifen."
}
```

Die Aussage darf nicht als aktuelle Reifenbestückung interpretiert werden.

## Test 19 – Service und mehrere Reifensätze

### Eingabe

> „CW AB 420, 68.200 Kilometer. Wechsel auf Winterreifen. Eingelagert werden vier Michelin Sommerreifen 225 45 17.“

### Erwartete Ausgabe

```json
{
  "license_plate": "CW-AB 420",
  "mileage_km": 68200,
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

Die Michelin-Sommerreifen dürfen nicht als montierter Satz gelten.

## Test 20 – Unverständlicher Modellname

### Eingabe

> „Vier Michelin äh Alpin irgendwas Winterreifen.“

### Erwartete Ausgabe

```json
{
  "manufacturer": "Michelin",
  "tire_type": "winter",
  "quantity": 4,
  "model": null,
  "field_status": {
    "model": "uncertain"
  },
  "review_required": true
}
```

## Test 21 – Vollständiges realistisches Beispiel

### Eingabe

> „CW PK 123, Kilometer 91.240. Vier Continental WinterContact TS 870, 225 45 R17. Vorne links sechs Komma fünf, vorne rechts sechs, hinten beide fünf. Hinten rechts außen leicht abgefahren. Sonst alles okay.“

### Erwartete Ausgabe

```json
{
  "license_plate": "CW-PK 123",
  "mileage_km": 91240,
  "manufacturer": "Continental",
  "model": "WinterContact TS 870",
  "tire_type": "winter",
  "quantity": 4,
  "width_mm": 225,
  "aspect_ratio": 45,
  "rim_diameter_inch": 17,
  "tread_front_left_mm": 6.5,
  "tread_front_right_mm": 6,
  "tread_rear_left_mm": 5,
  "tread_rear_right_mm": 5,
  "conditions": [
    {
      "condition": "outer_wear",
      "position": "rear_right"
    }
  ]
}
```

## Testanforderungen

Die Extraktion gilt für den MVP als ausreichend robust, wenn sie:

- explizit genannte Werte zuverlässig übernimmt,
- nicht genannte Werte nicht erfindet,
- Reifengrößen korrekt normalisiert,
- Werkstattformulierungen zuverlässig versteht,
- Korrekturen innerhalb einer Aufnahme berücksichtigt,
- Unsicherheiten sichtbar markiert und
- unrealistische Werte markiert, statt sie automatisch zu korrigieren.

Vor dem produktiven Test sollten die Beispiele durch mindestens 30–50 anonymisierte Werkstattformulierungen ergänzt werden.
