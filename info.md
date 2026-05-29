# FanControl IoT

Lokale Home-Assistant-Integration für **Brogachy EUT** und baugleiche
**Smart-Farmers-App-Tuya-Lüfter**.

Volle Steuerung im LAN — **22 Entities pro Gerät**: Fan, Modus, Temperatur
(°C), Feuchte, Countdown, Alarm-Indikator, Drehzahl-Slider, Brightness,
8 Schwellwerte (Auto + Alarm), 8 Trigger-Switches, Child Lock, Display-Einheit,
Sensor-Kalibrierungen — **ohne Tuya-Cloud-Traffic**.

## Highlights v0.5.2

- ✅ Komplett verifiziertes DP-Mapping für EUT-300B (alle 27 DPs gemessen)
- ✅ Hardware-Alarm als `binary_sensor` mit `device_class: problem`
- ✅ Notbetrieb-bewusste Fan-Entity (`is_on` über DP 103)
- ✅ Schwellwerte in °C eingebbar, intern °F konvertiert
- ✅ Trigger-Switches mit invertiertem Encoding gekapselt
- ✅ Auto-generiertes Dashboard via `custom:fancontrol-strategy` —
  3 Views (Steuerung / Schwellwerte / Einstellungen) ohne YAML-Schreiben

## Setup

`Device ID`, `Local Key`, `IP` und Protokoll-Version eintragen. Die Werte
holst du dir einmalig via `tinytuya wizard`. Danach: 100% lokal.

Details + Troubleshooting in der README.
