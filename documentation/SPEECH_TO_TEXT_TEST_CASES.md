# Speech-to-Text-Testfälle: deutsche Werkstattsprache

## Zweck und Abgrenzung

Dieser Katalog prüft ausschließlich das Rohtranskript einer deutschsprachigen
Werkstattaufnahme. Er prüft keine Extraktion in Fahrzeug- oder Reifenfelder;
dafür gibt es die [Extraktions-Testfälle](TEST_CASES.md). Alle Kennzeichen und
Fahrzeugangaben sind anonymisierte Testdaten.

Die neun Sätze stehen maschinenlesbar in
[`data/fixtures/german_workshop_stt_cases.json`](../data/fixtures/german_workshop_stt_cases.json).
Sie sind bewusst vollständige, natürlich formulierte Mechaniker-Sätze statt
einer Liste isolierter Werte.

## Automatisierte Tests

Aus `src/backend`:

```bash
python3 -m pytest tests/test_transcription_cases.py -q
```

Die Tests verwenden keinen API-Schlüssel und senden keine Audiodaten an einen
externen Dienst. Für jeden Satz prüfen sie den Adaptervertrag:

- Die Anfrage enthält `language: de`, den deutschen Werkstatt-Prompt und die
  Kfz-Schlüsselwörter.
- Ein vom Anbieter geliefertes Rohtranskript wird unverändert zurückgegeben.
- Der Korpus enthält Kennzeichen, die getrennten Kilometerstände `63.500` und
  `6.350`, `205/55 R16`, `225/40 R18`, die Profiltiefen `4,5` und `5,4` sowie
  Werte für vorne links, vorne rechts, hinten links und hinten rechts.
- Dokumentierte fehlerhafte oder mehrdeutige Anbieterantworten werden exakt
  zurückgegeben; der Adapter korrigiert oder ergänzt sie nicht.

Damit sind Übertragungsweg, Kontext und Schutz vor lokaler Nachbearbeitung
regressionsgetestet. Die akustische Erkennung eines externen Modells kann nur
mit einer tatsächlichen Aufnahme geprüft werden und ist deshalb Teil des
manuellen Laufs unten.

## Manueller Testlauf

Voraussetzungen: Testumgebung mit konfiguriertem Speech-to-Text-Anbieter, ein
Smartphone oder Tablet mit dem normalen Werkstatt-Mikrofon und eine ruhige sowie
eine übliche Werkstattumgebung. Für jeden Fall den Satz einmal natürlich
vorlesen, als WebM aufnehmen, an `POST /api/v1/audio/transcribe` senden und das
zurückgegebene Rohtranskript dokumentieren. Nicht langsamer oder deutlicher
sprechen als im Werkstattalltag.

Ein Fall besteht, wenn alle **kritischen Angaben** erhalten bleiben. Zulässig
sind nur diese Darstellungsvarianten: Leerzeichen statt Bindestrich im
Kennzeichen, Punkt oder kein Tausendertrennzeichen beim Kilometerstand,
`205/55 R16`, `205 55 R16` oder `205/55R16` (analog für `225/40 R18`) sowie
Komma oder Punkt bei Dezimalwerten. Hersteller, Modellname, Ziffern und die
Zuordnung von vorne / hinten / links / rechts dürfen nicht verändert oder
vertauscht werden.

| ID | Natürlich vorzulesender Satz | Kritische Angaben |
| --- | --- | --- |
| 01 | Beim Golf mit dem Kennzeichen B-AB 2746 stehen 128.450 Kilometer auf dem Tacho. Auf der Vorderachse fahren Michelin Pilot Sport 5 in 205/55 R16; vorne links messe ich 5,5 und vorne rechts 5 Millimeter Profil. | Kennzeichen, 128.450 km, Michelin Pilot Sport 5, Größe, Vorderachse, VL 5,5 / VR 5 |
| 02 | Für den Skoda mit M-KT 681 und 84.920 Kilometern: Continental WinterContact TS 870 in 205/55 R16. Auf der Hinterachse sind hinten links 6 und hinten rechts 6,5 Millimeter Profil. | Kennzeichen, 84.920 km, Continental WinterContact TS 870, Größe, Hinterachse, HL 6 / HR 6,5 |
| 03 | Beim BMW mit S-WR 908, Kilometerstand 212.305, sind vorne Goodyear Vector 4Seasons Gen-3 montiert. Die Vorderachse hat links 4,8, rechts 5,0 Millimeter, hinten sind es beidseitig 5,5. | Kennzeichen, Kilometerstand, Goodyear-Modell, vorne/links/rechts, hinten beidseitig, Profiltiefen |
| 04 | Kennzeichen CW-CT 225, 73.400 Kilometer: Bitte die Bridgestone Blizzak LM005, Größe 205/55 R16, einlagern. Vorne links 7 Millimeter, vorne rechts 6,5; hinten links 6 und hinten rechts 5,5. | Kennzeichen, Kilometerstand, Bridgestone-Modell, Größe, VL/VR/HL/HR und vier Profiltiefen |
| 05 | Bei F-PS 516 mit 56.780 Kilometern prüfen wir Hankook Ventus Prime 4 in 205/55 R16. An der Vorderachse ist vorne rechts das Profil mit 3,9 Millimetern niedriger als vorne links mit 4,4; an der Hinterachse links und rechts jeweils 4,8. | Kennzeichen, Kilometerstand, Hankook-Modell, Größe, beide Achsen, VR 3,9 / VL 4,4 / HA 4,8 |
| 06 | Für das Fahrzeug DA-TS 870 mit 101.015 Kilometern sind Michelin Alpin 6 Winterreifen in 205/55 R16 montiert. Hinten rechts haben wir 4 Millimeter, hinten links 4,5; vorne auf beiden Seiten 6. | Kennzeichen, Kilometerstand, Michelin Alpin 6, Größe, HR 4 / HL 4,5 / vorne beidseitig 6 |
| 07 | Kennzeichen M-AB 6350, Kilometerstand 63.500 Kilometer. Die Reifengröße ist 205/55 R16. | Kennzeichen-Buchstaben und -Ziffern, **63.500 km**, 205/55 R16 |
| 08 | Kennzeichen M-AB 6350, Kilometerstand 6.350 Kilometer. Die Reifengröße ist 225/40 R18. | Kennzeichen-Buchstaben und -Ziffern, **6.350 km**, 225/40 R18 |
| 09 | Profiltiefe: vorne links 4,5 Millimeter, vorne rechts 5,4 Millimeter, hinten links 5,4 Millimeter und hinten rechts 4,5 Millimeter. | VL 4,5 / VR 5,4 / HL 5,4 / HR 4,5; keine Vertauschung von 4,5 und 5,4 |

## Fehler und Mehrdeutigkeiten dokumentieren

Die Fälle 07–09 enthalten im Fixture unter `documented_raw_results` konkrete
Beispiele für problematische Anbieterantworten. Sie sind **keine** zulässigen
Varianten: Sie testen, dass das Rohtranskript ohne stillschweigende Korrektur
für die menschliche Prüfung erhalten bleibt.

| Fall | Rohtranskript-Beispiel | Bewertung | Dokumentation statt Korrektur |
| --- | --- | --- | --- |
| 07 | `M-AP 635` statt `M-AB 6350`; `6.350 Kilometer` statt `63.500 Kilometer` | falsch | Den erhaltenen Wert, die beabsichtigte Angabe und die Abweichung erfassen; weder Kennzeichen noch Kilometerstand erraten. |
| 08 | `225/40 oder R18` | mehrdeutig | Die Reifengröße nicht zu `225/40 R18` zusammensetzen; menschliche Klärung markieren. |
| 09 | `vorne 4,5 und 5,4`, `hinten 5,4 und 4,5` | mehrdeutig | Keine Links-rechts-Zuordnung aus der Reihenfolge ableiten. |

Pro Fall zusätzlich einmal unter üblichem Werkstattgeräusch und einmal mit der
normalen Aufnahme-Entfernung testen. Ein kritischer Fehler ist zum Beispiel
`rechts` statt `links`, `6.350` statt `63.500`, `R16` statt `R18`, eine
Verwechslung von `4,5` und `5,4`, ein anderer Reifenhersteller oder ein
fehlender Modellname. Solche Fehler oder Mehrdeutigkeiten mit Fall-ID, Gerät,
Browser, Umgebung, Modellkonfiguration, Originalaufnahme, beabsichtigter
Angabe und **unverändertem** erhaltenem Transkript erfassen; echte Kunden- oder
Fahrzeugdaten dürfen dabei nicht in das Repository gelangen.

## Abnahmeprotokoll

| Datum | Fall-ID | Gerät / Browser | Umgebung | Ergebnis | Abweichung / Ticket |
| --- | --- | --- | --- | --- |
|  |  |  | ruhig / Werkstattgeräusch | bestanden / fehlgeschlagen |  |
