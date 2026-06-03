# Ooni Connect Bluetooth for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/RookieIVG/ha-ooni)](https://github.com/RookieIVG/ha-ooni/releases)
[![Validate](https://github.com/RookieIVG/ha-ooni/actions/workflows/validate.yml/badge.svg)](https://github.com/RookieIVG/ha-ooni/actions/workflows/validate.yml)

A Home Assistant integration for the **Ooni Digital Thermometer** (standard on the Ooni Karu 16 and also available separately). It reads temperatures, battery level, and probe status directly via Bluetooth Low Energy (BLE).

> **Disclaimer:** This is an unofficial, community-built integration. It is **not affiliated with, endorsed by, or supported by Ooni**. "Ooni" and "Ooni Connect" are trademarks of their respective owners and are used here for descriptive purposes only.

## ✨ Features

- **Real-time temperatures:** Monitor the ambient sensors (Ambient A/B) and meat probes (Probe 1/2).
- **Connection monitor:** A dedicated binary sensor tracks whether the thermometer is currently connected or out of range. When the device disconnects, all measurement entities correctly become *unavailable* instead of showing stale values.
- **Hardware status:** See whether probes are plugged in and whether Eco mode is active.
- **Auto-discovery:** Home Assistant detects the device automatically when it is powered on and in range.
- **Localized:** English and German translations included.

## 📦 Installation

### Option 1: Via HACS (recommended)

This is a custom integration, so add it as a **Custom repository**:

1. Open HACS in Home Assistant.
2. Click the menu (three dots, top right) → **Custom repositories**.
3. Paste this repository's URL and choose category **Integration**.
4. Click **Add**, then install the integration.
5. **Restart Home Assistant.**

### Option 2: Manual

1. Download the repository.
2. Copy the `custom_components/ooni_connect` folder into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

> **Note:** The BLE backend is bundled with this integration, so nothing extra is downloaded on startup. `bleak` and `bleak-retry-connector` are provided by Home Assistant's built-in Bluetooth support.

## ⚙️ Configuration

1. Make sure Bluetooth is available on your Home Assistant host (built-in adapter or an ESPHome Bluetooth Proxy).
2. Turn on your Ooni thermometer.
3. Go to **Settings → Devices & Services**.
4. The device should be **discovered automatically**. If not, click **Add Integration**, search for **Ooni Connect**, and pick your device from the list.

## 📊 Available entities

| Name                     | Type          | Description                                          |
| ------------------------ | ------------- | ---------------------------------------------------- |
| Ambient temperature A    | Sensor        | Oven temperature (sensor A)                          |
| Ambient temperature B    | Sensor        | Oven temperature (sensor B)                          |
| Probe 1                  | Sensor        | Core temperature of probe 1                          |
| Probe 2                  | Sensor        | Core temperature of probe 2                          |
| Battery                  | Sensor        | Charge level in %                                    |
| Bluetooth connection     | Binary Sensor | `On` = connected, `Off` = out of range / off         |
| Probe 1 / 2 connected    | Binary Sensor | Whether the probe is physically plugged in           |
| Eco mode                 | Binary Sensor | Status of the power-saving mode                      |

## ❓ Troubleshooting

**Device is not found**

- The Ooni thermometer typically allows only **one** active Bluetooth connection. Make sure your phone (the Ooni app) is not currently connected.
- Briefly press the power button on the device to wake the display.

**Sensors are "Unavailable"**

- Check the **Bluetooth connection** sensor. If it is `Off`, the device is out of range or turned off. All measurement sensors are unavailable while disconnected.
- A probe sensor shows *unavailable* if no probe is plugged in (confirm with the matching **Probe connected** sensor).

**Enable debug logging**

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ooni_connect: debug
```

This also covers the bundled BLE backend, whose loggers live under `custom_components.ooni_connect.ooni_connect_bluetooth`.

## 🔧 Bundled backend

BLE communication is handled by the `ooni_connect_bluetooth` package, which is **vendored inside this integration** at `custom_components/ooni_connect/ooni_connect_bluetooth/`. There is no external dependency to install and nothing is downloaded at startup; `bleak` and `bleak-retry-connector` come from Home Assistant's built-in Bluetooth stack.

> **Keeping it in sync:** Because the backend is bundled, fixes made in the upstream [`ooni-connect-bluetooth`](https://github.com/RookieIVG/ooni-connect-bluetooth) repository do **not** flow in automatically — copy changed files into the vendored folder when you update.

## 🤝 Contributing

Issues and pull requests are welcome via the [issue tracker](https://github.com/RookieIVG/ha-ooni/issues). The `Validate` workflow runs `hassfest` and HACS validation on every push.

## 📄 License

Released under the [MIT License](LICENSE).
