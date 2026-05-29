# FanControl IoT

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-0.5.2-blue.svg)](https://github.com/virus18/fancontrol-iot/releases)

Home-Assistant-Integration für Tuya-basierte EC-Abluftventilatoren — speziell
**Brogachy EUT-Reihe** (EUT-100B / 150B / 200B / 250B / 300B) und baugleiche
Geräte aus der **Smart Farmers App** (App-Store-ID `1671760315`,
OEM-Hersteller ShenZhen Faithful Technology).

**100 % lokal über LAN.** Kein Tuya-Cloud-Traffic, nach dem einmaligen
Pairing kein Internet nötig.


## Highlights

- **22 Entities** pro Gerät — alles in HA bedienbar (Fan, Sensoren,
  Schwellwerte, Trigger-Switches, Kalibrierung, Child Lock, Brightness)
- **Notbetrieb-aware Fan-Entity** — `is_on` über DP 103 (Ist-Wert), sodass
  Auto-Boost bei Alarm korrekt angezeigt wird
- **Auto-generiertes Dashboard** via Lovelace-Strategy (`custom:fancontrol-strategy`) — 3 Views (Steuerung / Schwellwerte / Einstellungen) ohne YAML-Schreiben
- **Hardware-Alarm als `binary_sensor`** mit `device_class: problem` —
  perfekt für Push-Notifications
- **Schwellwerte in °C eingebbar**, intern automatisch nach °F konvertiert
- **Trigger-Switches gekapselt** — interne `"0"=ON / "1"=OFF`-Invertierung
  ist für HA-Nutzer unsichtbar
- **Standalone-Web-UI + CLI** im Schwester-Repo zum Mappen unbekannter
  Geräte-Varianten

## Was du in HA bekommst (pro Gerät)

| Plattform | Entity (Beispiel) | Funktion |
|-----------|--------------------|----------|
| `fan` | `fan.<name>` | Power + Drehzahl 0–100 % (Stufe 1–10), Auto-Boost-bewusst |
| `select` | `select.<name>_mode` | Betriebsmodus: `ON / TIMER / AUTO / ALARM` |
| `sensor` | `sensor.<name>_temperature` | Innentemperatur in °C (auto-konvertiert aus °F) |
| `sensor` | `sensor.<name>_humidity` | Innenfeuchte in % |
| `sensor` | `sensor.<name>_countdown` | TIMER-Restzeit in Sekunden |
| `binary_sensor` | `binary_sensor.<name>_alarm_triggered` | Hardware-Alarm aktiv |
| `number` | `number.<name>_speed_stage` | Drehzahl-Slider 0–10 (redundant zum Fan, aber bequem) |
| `number` | `number.<name>_brightness` | Display-Helligkeit (1–3) |
| `number` × 4 | `…_auto_high_temp` etc. | Auto-Modus-Schwellwerte (°C / %) |
| `number` × 4 | `…_alarm_high_temp` etc. | Alarm-Modus-Schwellwerte (°C / %) |
| `number` × 2 | `…_temp_calibration` etc. | Sensor-Offset (°F-Schritte) |
| `switch` × 4 | `…_auto_high_temp` etc. | Auto-Trigger an/aus |
| `switch` × 4 | `…_alarm_high_temp` etc. | Alarm-Trigger an/aus |
| `switch` | `…_child_lock` | Kindersicherung |
| `switch` | `…_display_celsius` | Display-Einheit °C/°F |

## Installation

### Via HACS (empfohlen)

1. HACS öffnen → **Integrations** → ⋮ oben rechts → **Custom repositories**
2. URL `https://github.com/virus18/fancontrol-iot` eintragen,
   Kategorie **Integration**
3. Nach **FanControl IoT** suchen und installieren
4. Home Assistant neu starten

### Manuell

```bash
git clone https://github.com/virus18/fancontrol-iot.git
cp -r fancontrol-iot/custom_components/fancontrol_iot /config/custom_components/
```

Anschließend Home Assistant neu starten.

## Setup

### 1. `local_key` besorgen

Da das Gerät über die Tuya-Cloud provisioniert wird, brauchst du
**einmalig** den `local_key`:

1. Lüfter in der **Smart Life App** oder **Smart Farmers App** pairen
   *(nur 2,4-GHz-WLAN — Tuya unterstützt kein 5 GHz)*
2. Auf [iot.tuya.com](https://iot.tuya.com) einen kostenlosen Account anlegen
3. **Cloud → Development → Create Cloud Project**, Industry **Smart Home**,
   Data Center **Central Europe** (für deutsche App-Accounts)
4. **Devices → Link App Account → Add App Account → Tuya App Account
   Authorization** → QR-Code in der Smart-Life-App scannen
   *(in der App: Tab „Ich" → Scan-Symbol oben rechts)*
5. Im Projekt unter **Overview** Access-ID + Secret merken
6. In der Konsole:
   ```bash
   pip install tinytuya
   python -m tinytuya wizard
   ```
   Wizard fragt nach den Daten und schreibt `devices.json` mit `id`, `key`,
   `ip`, `version`

### 2. Integration hinzufügen

In Home Assistant: **Settings → Devices & Services → Add Integration →
FanControl IoT**

| Feld | Beispiel |
|------|----------|
| **Name** | `Lüfter Technikraum` |
| **Device ID** | aus `devices.json`, Feld `id` |
| **Local Key** | aus `devices.json`, Feld `key` |
| **IP-Adresse** | aus `devices.json`, Feld `ip` (oder per LAN-Scan ermittelt) |
| **Tuya-Protokoll-Version** | aus `devices.json`, meist `3.4` |

Nach erfolgreichem Setup erscheinen alle 22 Entities am Device.

### 3. Dashboard automatisch generieren

Die Integration bringt eine **Lovelace-Strategy** mit, die ein
komplettes Dashboard mit 3 Views auto-generiert (Steuerung / Schwellwerte
/ Einstellungen).

1. **Settings → Dashboards → + Add Dashboard**
2. Titel + Pfad eingeben (z. B. `Lüfter`)
3. Dashboard öffnen → **Edit** → ⋮ → **Raw configuration editor**
4. Alles ersetzen durch:
   ```yaml
   strategy:
     type: custom:fancontrol-strategy
   views: []
   ```
5. **Save** — fertig.

Nur eine einzelne View ins existierende Dashboard:

```yaml
views:
  - title: Lüfter
    strategy:
      type: custom:fancontrol-strategy
      view: main      # | trigger | settings
```

## Backend-Settings (HA → Integration → Configure)

Alles ohne YAML-Editor über das HA-UI nachjustierbar:

| Untermenü | Inhalt |
|-----------|--------|
| **Connection** | Device ID, Local Key, IP, Protokoll-Version |
| **Polling** | `scan_interval` (3–600 s), `socket_timeout` (1–30 s) |
| **DP Mapping** | Override der 8 Standard-DPs für abweichende Modelle |
| **Speed + Skalierung** | speed_min/max, temp_scale, temp_unit_input (°F/°C), mode_options |
| **Externe Sensoren** | Outside-Temp / Weather / Notify-Service für Cards |
| **Boost-Defaults** | Boost-Dauer, -Drehzahl, Auto-Boost-Switch |

Änderungen werden sofort wirksam — die Integration lädt sich automatisch
neu.

## DP-Mapping (EUT-300B, vollständig verifiziert)

Alle DPs per Live-Observer durch die Smart-Life-App getoggelt und
bestätigt. Vollständige Tabelle mit allen Wertebereichen, Encoding-Details
und Cloud-vs-LAN-Vergleich in [`docs/dp-mapping.md`](docs/dp-mapping.md).

| DP | Funktion | Encoding | Konfigurierbar |
|----|----------|----------|----------------|
| 1 | Online-Flag | bool, immer `true` | — |
| 2 | Modus | enum `ON/TIMER/AUTO/ALARM` | ✓ |
| 8 | Feuchte (Ist) | int `%` | — (read-only) |
| 9 | Temperatur (Ist) | int `°F` | — (read-only) |
| 101 | Display-Helligkeit | int 1–3 | ✓ |
| 102 | **Drehzahl + Power** | int 0–10 (0 = aus) | ✓ |
| 103 | Drehzahl (Ist) | int (Spiegel + Notbetrieb) | — (read-only) |
| 105 | Countdown / Alarm-Flag | str: `"0"` idle, `"8"` Alarm aktiv | — |
| 106–113 | 8× Schwellwerte | int °F bzw. % | ✓ |
| 114 | Child Lock | str `"0"=unlock`/`"1"=lock` | ✓ |
| 115 | Display-Einheit | str `"1"=°C`/`"0"=°F` | ✓ |
| 116–123 | 8× Trigger-Switches | str **invertiert** `"0"=ON`/`"1"=OFF` | ✓ |
| 124, 125 | Temp- / Humid-Kalibrierung | int Offset | ✓ |

## Architektur-Highlights

### `fan.py` — Notbetrieb-bewusst

```python
@property
def is_on(self) -> bool | None:
    # actual_speed (DP 103) ist die Quelle der Wahrheit — deckt auch
    # den Notbetrieb ab (DP 103 = 10 bei Alarm, obwohl DP 102 = 0).
    if self.coordinator.power_and_speed_share_dp:
        actual = self.coordinator.actual_speed()
        return None if actual is None else actual > 0
    return bool(self.coordinator.dp_value("power"))
```

### `switch.py` — Inverted Trigger gekapselt

```python
async def async_set_trigger(self, role: str, on: bool) -> None:
    """HA-ON → '0', HA-OFF → '1' (Geräte-Encoding ist invertiert)."""
    await self.async_set_role(role, "0" if on else "1")
```

### `number.py` — °C ↔ °F transparent

```python
async def async_set_native_value(self, value: float) -> None:
    # User-Eingabe in °C → in °F konvertieren vor dem Schreiben
    await self.coordinator.async_set_role(self._role, _c_to_f(value))
```

### `binary_sensor.py` — Hardware-Alarm

```python
@property
def is_on(self) -> bool:
    return self.coordinator.is_alarm_active   # DP 105 == "8"
```

## Troubleshooting

**„Connection failed" beim Setup**
→ IP falsch, Gerät im 5-GHz-WLAN (Tuya kann nur 2.4), oder falsche
Protokoll-Version (probier 3.3 / 3.4 / 3.5)

**„No data" / nur leere DPs**
→ Verbindung klappt, aber `tinytuya` bekommt keine Werte. Andere
Protokoll-Version probieren.

**Temperatur zeigt z. B. −13 °C statt 22 °C**
→ Alte `temp_scale = 0.1` aus früherer Setup-Version hängt in den Options.
Fix: **Integration → Configure → Speed Range + Scaling →
`temp_scale = 1.0`** setzen.

**Mode-Dropdown zeigt `manual/auto/timer/smart/sleep` statt
`ON/TIMER/AUTO/ALARM`**
→ Gleicher Carry-over-Effekt. **Configure → Speed Range + Scaling →
Mode options** korrigieren oder Integration löschen + neu hinzufügen.

**Lokaler Key wurde ungültig**
→ Nach Re-Pairing oder Firmware-Update vergibt Tuya einen neuen Key.
`tinytuya wizard` erneut ausführen und den neuen Key in der
Integration-Konfig eintragen.

**Strategy-Dashboard rendert nicht**
→ Browser-Cache: `Strg+Shift+R`. Falls weiterhin leer → F12-Konsole:
beim Laden müsste `FANCONTROL-STRATEGY v0.5.2` erscheinen.

## Verifizierte Geräte

- ✅ Brogachy **EUT-300B** (vollständig getestet, 27 DPs gemessen)
- 🟡 Brogachy EUT-100B / 150B / 200B / 250B (baugleich — DP-Layout
  vermutlich identisch)
- 🟡 Smart-Farmers-Whitelabel von Faithful Technology (gleiche App,
  gleiche Cloud)

PRs für weitere verifizierte Geräte willkommen — siehe Issue-Template.

## Lizenz

MIT — siehe [LICENSE](LICENSE).

## Quellen + Inspiration

- [tinytuya](https://github.com/jasonacox/tinytuya) — Python-Tuya-LAN-Lib
- [tuya-local](https://github.com/make-all/tuya-local) — HA-Tuya generisch
- [LocalTuya](https://github.com/rospogrigio/localtuya) — alter Klassiker
