/*
 * FanControl IoT — Lovelace-Dashboard-Strategy
 *
 * Generiert automatisch 3 Views (Lüfter, Schwellwerte, Einstellungen) für
 * jedes konfigurierte FanControl-IoT-Gerät. Erkennt die echten Entity-IDs
 * via hass.entities (Domain-Lookup), keine manuelle Konfiguration nötig.
 *
 * Verwendung in einem Dashboard (Settings → Dashboards → Neu → leer
 * → ⋮ → Raw-Configuration-Editor):
 *
 *   strategy:
 *     type: custom:fancontrol-strategy
 *   views: []          # bleibt leer, Strategy füllt sie
 *
 * Oder pro View:
 *   views:
 *     - strategy:
 *         type: custom:fancontrol-strategy
 *         view: main      # | trigger | settings
 *
 * Wird von der Integration automatisch als Frontend-Resource registriert.
 */

const STRATEGY_VERSION = "0.5.2";
const PLATFORM = "fancontrol_iot";

// ---- Strategy-Klasse ------------------------------------------------
class FanControlStrategy extends HTMLElement {
  static async generate(config, hass) {
    const devices = collectDevices(hass);
    if (!devices.length) {
      return {
        title: "FanControl IoT",
        views: [{
          title: "Setup",
          cards: [{
            type: "markdown",
            content:
              "**Keine FanControl-IoT-Geräte gefunden.**\n\n" +
              "Bitte erst unter *Settings → Devices & Services* die Integration einrichten.",
          }],
        }],
      };
    }

    // Wenn nur eine bestimmte Sub-View gewünscht ist
    if (config.view) {
      const dev = devices[0]; // nur erstes Gerät für Single-View
      switch (config.view) {
        case "main":     return buildMainView(dev);
        case "trigger":  return buildTriggerView(dev);
        case "settings": return buildSettingsView(dev);
        default: break;
      }
    }

    // Default: komplettes Dashboard mit 3 Views pro Gerät
    const views = [];
    for (const dev of devices) {
      views.push(buildMainView(dev));
      views.push(buildTriggerView(dev));
      views.push(buildSettingsView(dev));
    }
    return { title: "Lüftung", views };
  }
}

// ---- Geräte aus hass.entities sammeln -------------------------------
function collectDevices(hass) {
  const byDevice = new Map();
  for (const ent of Object.values(hass.entities || {})) {
    if (ent.platform !== PLATFORM) continue;
    const did = ent.device_id;
    if (!did) continue;
    if (!byDevice.has(did)) byDevice.set(did, []);
    byDevice.get(did).push(ent.entity_id);
  }
  const out = [];
  for (const [device_id, entity_ids] of byDevice) {
    const dev = hass.devices?.[device_id];
    const name = dev?.name_by_user || dev?.name || "FanControl";
    out.push({ device_id, name, entity_ids, lookup: indexEntities(entity_ids) });
  }
  return out;
}

// Index Entity-IDs nach role-suffix (translation_key) für schnelles Lookup
function indexEntities(entity_ids) {
  const idx = {};
  for (const eid of entity_ids) {
    const [domain, rest] = splitEid(eid);
    if (!domain) continue;
    // Suffix nach letztem "_" — nicht perfekt, aber gut genug für unsere Keys
    // Stattdessen: probiere alle bekannten Suffixe der Reihe nach
    for (const key of KNOWN_KEYS) {
      const needle = "_" + key;
      if (rest.endsWith(needle) || rest === key) {
        // Domain-Filter: nur passende Plattform
        idx[`${domain}.${key}`] = eid;
        idx[key] = idx[key] || eid;
      }
    }
  }
  return idx;
}

function splitEid(eid) {
  const dot = eid.indexOf(".");
  if (dot < 0) return [null, null];
  return [eid.slice(0, dot), eid.slice(dot + 1)];
}

// Bekannte translation_keys / Entity-Suffixe
const KNOWN_KEYS = [
  "fan", "mode",
  "temperature", "humidity", "countdown",
  "alarm_triggered",
  "speed_stage", "brightness",
  "temp_calibration", "humid_calibration",
  "auto_high_temp", "auto_high_humid", "auto_low_temp", "auto_low_humid",
  "alarm_high_temp", "alarm_high_humid", "alarm_low_temp", "alarm_low_humid",
  "child_lock", "display_celsius",
];

// Lookup-Helfer: bekommt Domain+Key, returns Entity-ID oder null
function E(dev, domain, key) {
  return dev.lookup[`${domain}.${key}`] || null;
}

// ---- View-Builder ---------------------------------------------------

function buildMainView(dev) {
  const fan      = E(dev, "fan",           "fan")            || dev.entity_ids.find(e => e.startsWith("fan."));
  const temp     = E(dev, "sensor",        "temperature");
  const humid    = E(dev, "sensor",        "humidity");
  const countdwn = E(dev, "sensor",        "countdown");
  const alarm    = E(dev, "binary_sensor", "alarm_triggered");
  const mode     = E(dev, "select",        "mode");
  const speedNum = E(dev, "number",        "speed_stage");
  const bright   = E(dev, "number",        "brightness");

  const cards = [];

  // 1. Hero-Reihe — Fan + Temp + Humid
  cards.push({
    type: "horizontal-stack",
    cards: [
      fan && {
        type: "tile",
        entity: fan,
        name: dev.name,
        icon: "mdi:fan",
        color: "cyan",
        features: [{ type: "fan-speed" }],
      },
      temp  && { type: "tile", entity: temp,  name: "Temperatur", color: "orange" },
      humid && { type: "tile", entity: humid, name: "Feuchte",    color: "blue"   },
    ].filter(Boolean),
  });

  // 2. Alarm-Banner (conditional)
  if (alarm) {
    cards.push({
      type: "conditional",
      conditions: [{ entity: alarm, state: "on" }],
      card: {
        type: "markdown",
        content:
          "## 🚨 ALARM AKTIV\n" +
          "Der Lüfter läuft im **Notbetrieb auf Stufe 10**. " +
          "Eine Schwelle wurde überschritten.",
      },
    });
  }

  // 3. Schnellsteuerung
  const ctrlEnts = [];
  if (speedNum) ctrlEnts.push({ entity: speedNum, name: "Drehzahl (0–10)" });
  if (mode)     ctrlEnts.push({ entity: mode,     name: "Betriebsmodus"   });
  if (ctrlEnts.length) {
    cards.push({
      type: "entities",
      title: "Steuerung",
      show_header_toggle: false,
      entities: ctrlEnts,
    });
  }

  // 4. Status
  const statusEnts = [temp, humid, countdwn, alarm, bright]
    .filter(Boolean)
    .map(e => ({ entity: e }));
  if (statusEnts.length) {
    cards.push({
      type: "entities",
      title: "Status",
      show_header_toggle: false,
      entities: statusEnts,
    });
  }

  return { title: `${dev.name} · Lüfter`, path: "main", icon: "mdi:fan", cards };
}

function buildTriggerView(dev) {
  const cards = [];

  // AUTO
  cards.push(buildThresholdCard(dev, "🤖 Auto-Modus · Schwellwerte", [
    { kind: "temp",  high: "auto_high_temp",  low: "auto_low_temp"  },
    { kind: "humid", high: "auto_high_humid", low: "auto_low_humid" },
  ]));

  // ALARM
  cards.push(buildThresholdCard(dev, "🚨 Alarm-Modus · Schwellwerte", [
    { kind: "temp",  high: "alarm_high_temp",  low: "alarm_low_temp"  },
    { kind: "humid", high: "alarm_high_humid", low: "alarm_low_humid" },
  ]));

  return { title: `${dev.name} · Schwellwerte`, path: "trigger", icon: "mdi:thermometer-lines", cards: cards.filter(c => c.entities.length > 0) };
}

function buildThresholdCard(dev, title, groups) {
  const entities = [];
  for (const g of groups) {
    const label = g.kind === "temp" ? "Temperatur (°C)" : "Feuchte (%)";
    entities.push({ type: "section", label });
    const highNum = E(dev, "number", g.high);
    const highSw  = E(dev, "switch", g.high);
    const lowNum  = E(dev, "number", g.low);
    const lowSw   = E(dev, "switch", g.low);
    if (highNum) entities.push({ entity: highNum, name: "Hoch" });
    if (highSw)  entities.push({ entity: highSw,  name: "↑ Hoch aktiv" });
    if (lowNum)  entities.push({ entity: lowNum,  name: "Tief" });
    if (lowSw)   entities.push({ entity: lowSw,   name: "↓ Tief aktiv" });
  }
  return { type: "entities", title, show_header_toggle: false, entities };
}

function buildSettingsView(dev) {
  const cards = [];

  const childLock = E(dev, "switch", "child_lock");
  const dispC     = E(dev, "switch", "display_celsius");
  const bright    = E(dev, "number", "brightness");
  const tempCal   = E(dev, "number", "temp_calibration");
  const humidCal  = E(dev, "number", "humid_calibration");

  const settings = [childLock, dispC, bright].filter(Boolean).map(e => ({ entity: e }));
  if (settings.length) {
    cards.push({
      type: "entities",
      title: "🔧 Gerätesettings",
      show_header_toggle: false,
      entities: settings,
    });
  }

  const cals = [tempCal, humidCal].filter(Boolean).map(e => ({ entity: e }));
  if (cals.length) {
    cards.push({
      type: "entities",
      title: "🎯 Sensor-Kalibrierung",
      show_header_toggle: false,
      entities: [
        { type: "section", label: "Offset wird vom Gerät direkt auf den Messwert addiert" },
        ...cals,
      ],
    });
  }

  return { title: `${dev.name} · Einstellungen`, path: "settings", icon: "mdi:cog", cards };
}

// ---- Registrierung --------------------------------------------------
customElements.define("ll-strategy-fancontrol-strategy", FanControlStrategy);
customElements.define("ll-strategy-dashboard-fancontrol-strategy", FanControlStrategy);
customElements.define("ll-strategy-view-fancontrol-strategy", FanControlStrategy);

console.info(
  `%c FANCONTROL-STRATEGY %c v${STRATEGY_VERSION} `,
  "background:#00d4ff;color:#000;font-weight:700;border-radius:3px 0 0 3px;",
  "background:#13151c;color:#00d4ff;border-radius:0 3px 3px 0;"
);
