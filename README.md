# FanControl IoT

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home-Assistant-Integration fuer Tuya-basierte EC-Abluftventilatoren — speziell
**Brogachy EUT-Reihe** (EUT-100B / 150B / 200B / 250B / 300B) und baugleiche
Geräte aus der **Smart Farmers App** von ShenZhen Faithful Technology.

**Steuerung 100% lokal über das LAN** — kein Tuya-Cloud-Traffic, nach dem
einmaligen Pairing kein Internet noetig.

## Was du bekommst

Pro Geraet vier Plattformen:

| Entity                          | Funktion                                      |
|---------------------------------|-----------------------------------------------|
| `fan.<name>`                    | Power + Drehzahl (10 Stufen via Prozent)      |
| `sensor.<name>_temperature`     | gemessene Temperatur                          |
| `sensor.<name>_humidity`        | gemessene Feuchte                             |
| `number.<name>_target_temperature` | Sollwert Temperatur                        |
| `number.<name>_target_humidity` | Sollwert Feuchte                              |
| `number.<name>_timer`           | Countdown-Timer (Sekunden)                    |
| `select.<name>_mode`            | Betriebsmodus (manual / auto / timer / ...)   |

## Installation

### Via HACS (empfohlen)

1. HACS oeffnen → **Integrations** → die drei Punkte oben rechts → **Custom repositories**.
2. URL dieses Repos eintragen, Kategorie: **Integration**.
3. Suche nach **"FanControl IoT"** und installieren.
4. Home Assistant neu starten.

### Manuell

```bash
git clone https://github.com/virus18/fancontrol-iot.git
cp -r fancontrol-iot/custom_components/fancontrol_iot /config/custom_components/
```

Dann Home Assistant neu starten.

## Setup

### 1. local_key besorgen

Da das Geraet ueber Tuya-Cloud provisioniert wird, brauchst du **einmalig**
den `local_key`:

1. Geraet in der **Smart Life App** (oder Smart Farmers) pairen.
2. Auf [iot.tuya.com](https://iot.tuya.com) einen kostenlosen Account anlegen.
3. Cloud-Projekt anlegen (Smart Home, Datacenter passend zur App-Region — bei
   Smart-Life-DE = Central Europe).
4. Devices → Link App Account → QR mit der App scannen.
5. Auf der Konsole `python -m tinytuya wizard` ausfuehren — Wizard schreibt
   `devices.json` mit `id`, `key`, `ip`, `ver`.

Details: siehe Repo [virus18/fancontrol-iot/wiki](https://github.com/virus18/fancontrol-iot/wiki).

### 2. Integration hinzufuegen

In HA: **Settings → Devices & Services → Add Integration → FanControl IoT**.

Felder ausfuellen:
- **Name** — Anzeigename (z.B. "Halle Abluft")
- **Device ID** — aus `devices.json` (`id`-Feld)
- **Local Key** — aus `devices.json` (`key`-Feld)
- **IP-Adresse** — aus `devices.json` (`ip`-Feld)
- **Version** — 3.3, 3.4 oder 3.5 (im Zweifel 3.4)

Wenn die Verbindung steht: Geraet erscheint mit allen Entities.

## DP-Mapping

Die Integration nutzt das Standard-DP-Layout fuer Tuya-Klima/Fan-Geraete:

| DP  | Funktion             |
|-----|----------------------|
| 1   | Power (bool)         |
| 2   | Mode (str enum)      |
| 3   | Drehzahl (int 1..10) |
| 18  | Temp Ist (int, /10)  |
| 19  | Humid Ist (int)      |
| 22  | Soll-Temperatur      |
| 23  | Soll-Feuchte         |
| 26  | Timer (Sekunden)     |

Falls dein Geraet ein abweichendes DP-Layout hat, ist [das mitgelieferte
Setup-Tool](https://github.com/virus18/fancontrol-iot/tree/main/tools) im
Schwester-Repo hilfreich, um das Mapping interaktiv zu finden.

## Bekannte unterstuetzte Geraete

- Brogachy EUT-100B / 150B / 200B / 250B / 300B (verifiziert: ___)
- baugleiche EC-Inline-/Wandventilatoren von Faithful Technology

Falls du ein Geraet zum Laufen gebracht hast: bitte ein PR mit Eintrag hier.

## Troubleshooting

**"Connection failed"** beim Setup
→ IP falsch, Geraet im 5-GHz-WLAN (Tuya kann nur 2.4 GHz), oder falsche Version.

**"No data"**
→ Verbindung klappt, aber `tinytuya` bekommt keine DPs. Andere Protokoll-Version
   probieren (3.3/3.4/3.5).

**Lokaler Key wurde ungueltig**
→ Bei Re-Pairing oder Firmware-Update wird der `local_key` neu vergeben.
   `tinytuya wizard` nochmal laufen lassen, in der Integration-Konfiguration
   den neuen Key eintragen (Options-Flow).

## Lizenz

MIT — siehe [LICENSE](LICENSE).

## Quellen + Inspiration

- [tinytuya](https://github.com/jasonacox/tinytuya)
- [tuya-local](https://github.com/make-all/tuya-local)
- [LocalTuya](https://github.com/rospogrigio/localtuya)
