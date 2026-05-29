# DP-Mapping — Brogachy EUT-300B (Smart Farmers / Tuya)

Vollständig per Live-Observer durch die Smart-Life-App **direkt am Gerät
gemessen**. Jeder DP wurde via Toggle-und-Diff bestätigt.

- **Gerätemodell:** Brogachy EUT-300B
- **App:** Smart Farmers (App-Store-ID `1671760315`, OEM ShenZhen
  Faithful Technology) bzw. die deutsche Smart-Life-App
- **Tuya-Kategorie:** `xfj` (Frischluft-Ventilator)
- **Produkt-Spec aus Cloud:** Modell `Ec-v1.0`, Schema-ID `hqldzgqpsyr1pw8c`
- **Protokoll-Version:** **3.4**
- **Stand:** 2026-05-29

## Wichtige Encoding-Konventionen

1. **Power + Drehzahl teilen sich einen DP** (DP 102): `0` = aus, `1–10` =
   Drehzahlstufe. DP 1 ist nur ein Online-Flag und immer `true`.
2. **Temperatur kommt in °F** (DP 9, DP 106 / 108 / 110 / 112, DP 124).
   HA rechnet automatisch nach °C um.
3. **Trigger-Switches** (DP 116–123) sind **invertiert** kodiert:
   `"0"` = ON, `"1"` = OFF. Die Switch-Entities in HA kapseln das, du
   bedienst sie ganz normal.
4. **Setting-Switches** (DP 114 Child Lock, DP 115 Unit) sind **normal**:
   `"1"` = aktiv.
5. **DP 105 ist überladen:** Im TIMER-Modus zählt es die verbleibenden
   Sekunden, bei aktivem Alarm steht hier `"8"` als Hardware-Flag. Die
   Integration trennt das in `binary_sensor.alarm_triggered` und
   `sensor.countdown`.
6. **Setpoint vs. Ist-Drehzahl:** DP 102 ist dein Setpoint, DP 103 ist
   was das Gerät **wirklich** macht. Bei Alarm boostet das Gerät
   eigenständig auf Stufe 10, dann gilt DP 103 = 10 obwohl DP 102 = 0.
   Die Fan-Entity in HA leitet `is_on` deshalb aus DP 103 ab.

## Komplette DP-Tabelle (27 aktive DPs)

| DP | Typ | Funktion | Wertebereich | Encoding | R/W | Status |
|----|-----|----------|--------------|----------|-----|--------|
| 1   | bool | Online-Flag (immer `true`) | `true` | — | R | ✓ |
| 2   | str  | Modus | `ON` / `TIMER` / `AUTO` / `ALARM` | enum | R/W | ✓ |
| 8   | int  | Feuchte (Ist) | `0–100` (`%`) | — | R | ✓ |
| 9   | int  | Temperatur (Ist) | `°F` (z.B. `71` = 21.7 °C) | — | R | ✓ |
| 101 | int  | Display-Helligkeit | `1–3` | — | R/W | ✓ |
| 102 | int  | **Drehzahl + Power** | `0–10` (0 = aus) | — | R/W | ✓ |
| 103 | int  | Drehzahl (Ist, inkl. Notbetrieb) | `0–10` | Spiegel von 102, **außer** bei Alarm | R | ✓ |
| 104 | int  | (existiert auf diesem Gerät **nicht**) | — | — | — | — |
| 105 | str  | **Alarm-Flag / Countdown** | `"0"` idle, `"8"` Alarm aktiv, sonst Restsekunden im TIMER-Modus | — | R | ✓ |
| 106 | int  | Auto-High Temp | `°F` | — | R/W | ✓ |
| 107 | int  | Auto-High Humid | `%` | — | R/W | ✓ |
| 108 | int  | Auto-Low Temp | `°F` | — | R/W | ✓ |
| 109 | int  | Auto-Low Humid | `%` | — | R/W | ✓ |
| 110 | int  | Alarm-High Temp | `°F` | — | R/W | ✓ |
| 111 | int  | Alarm-High Humid | `%` | — | R/W | ✓ |
| 112 | int  | Alarm-Low Temp | `°F` | — | R/W | ✓ |
| 113 | int  | Alarm-Low Humid | `%` | — | R/W | ✓ |
| 114 | str  | Child Lock | `"0"` unlock, `"1"` lock | **normal** | R/W | ✓ |
| 115 | str  | Display-Einheit | `"1"` °C, `"0"` °F | **normal** | R/W | ✓ |
| 116 | str  | Switch: Auto-High Temp | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 117 | str  | Switch: Auto-High Humid | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 118 | str  | Switch: Auto-Low Temp | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 119 | str  | Switch: Auto-Low Humid | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 120 | str  | Switch: Alarm-High Temp | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 121 | str  | Switch: Alarm-High Humid | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 122 | str  | Switch: Alarm-Low Temp | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 123 | str  | Switch: Alarm-Low Humid | `"0"` = ON, `"1"` = OFF | **invertiert** | R/W | ✓ |
| 124 | int  | Temp-Kalibrierung | Offset in `°F`, `-20…+20` | additive auf DP 9 | R/W | ✓ |
| 125 | int  | Humid-Kalibrierung | Offset in `%`, `-20…+20` | additive auf DP 8 | R/W | ✓ |
| 126 | str  | Status-Flag (geräte-intern) | `"0"` / `"8"` | unklar | R | – |

## Verhalten im Alarm-Fall (gemessen)

Wenn eine Trigger-Schwelle ausgelöst hat:

| DP | Vorher | Nachher | Bedeutung |
|----|--------|---------|-----------|
| 105 | `"0"` | **`"8"`** | Alarm-Flag aktiv |
| 103 | `0` (laut Setpoint aus) | **`10`** | Gerät boostet selbständig auf Maximum |
| 102 | `0` | `0` | Setpoint bleibt unverändert |
| `binary_sensor.alarm_triggered` | `off` | **`on`** | HA-Entity meldet sauber |

Wenn der Trigger-Switch wieder deaktiviert wird, fährt der Lüfter zurück
auf den Setpoint (DP 102) und DP 105 fällt auf `"0"`.

## Smart-Life-App-Layout → DP-Mapping

So heißen die Felder in der Smart-Life-App und auf welchen DPs sie liegen:

| App-Feld | DP |
|----------|-----|
| Work Mode | 2 |
| Humidity (read-only) | 8 |
| Temperature (read-only) | 9 |
| Alarm triggered (read-only) | abgeleitet aus DP 105 |
| Countdown (read-only) | abgeleitet aus DP 105 |
| Brightness | 101 |
| Running Speed (read-only) | 103 |
| Fan Speed Setting | 102 |
| Auto-High Temp | 106 |
| Auto-High Humid | 107 |
| Auto-Low Temp | 108 |
| Auto-Low Humid | 109 |
| Alarm-High Temp | 110 |
| Alarm-High Humid | 111 |
| Alarm-Low Temp | 112 |
| Alarm-Low Humid | 113 |
| Auto-High temp switch (P7) | 116 |
| Auto-High humid switch (P9) | 117 |
| Auto-Low temp switch | 118 |
| Auto-Low humid switch | 119 |
| Alarm-High temp switch | 120 |
| Alarm-High humid switch | 121 |
| Alarm-Low temp switch | 122 |
| Alarm-Low humid switch | 123 |
| Child Lock (P5) | 114 |
| Unit | 115 |
| Temp calibration | 124 |
| Humid calibration | 125 |

## Cloud-Spec vs. tatsächliches Verhalten

Die Tuya-Cloud listet im Produkt-Datenmodell für dieses Gerät **nur 3 DPs**:

```json
{
  "1":  { "code": "switch",           "type": "Boolean"  },
  "8":  { "code": "humidity_indoor",  "type": "Integer", "unit": "%"  },
  "9":  { "code": "temp_indoor",      "type": "Integer", "unit": "°F" }
}
```

Die anderen **24 DPs** sind nicht im Cloud-Spec dokumentiert, werden aber
vom Gerät über das lokale LAN-Protokoll voll unterstützt. Sie wurden alle
empirisch per Toggle-und-Diff in der App gemessen und semantisch verdrahtet.

Die Cloud-Behauptung „DP 1 = switch" ist **irreführend** — DP 1 ist auf
diesem Gerät tatsächlich nur ein Online-Flag, das wirkliche
Power-/Drehzahl-Verhalten geht über DP 102.

## Compatibility-Hinweis für andere EUT-Modelle

Brogachy bietet die EUT-Reihe in mehreren Größen an (100B / 150B / 200B /
250B / 300B). Da alle die gleiche Smart-Farmers-App nutzen und denselben
OEM-Hersteller haben, ist das DP-Layout **mit hoher Wahrscheinlichkeit
identisch**. Bestätigte Geräte sammeln wir in der README unter
„Verifizierte Geräte". PRs willkommen.

Falls dein EUT-Modell abweicht, kannst du das DP-Mapping in
**Settings → Devices & Services → FanControl IoT → Configure → DP Mapping**
manuell überschreiben.
