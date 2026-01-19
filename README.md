# Ooni Connect Bluetooth for Home Assistant

![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

A Home Assistant integration for the **Ooni Digital Thermometer** (standard on the Ooni Karu 16 and also available separately). This integration reads temperatures, battery levels, and probe status directly via Bluetooth Low Energy (BLE).

## ✨ Features

* **Real-time Temperatures:** Monitor ambient sensors (Ambient A/B) and meat probes (Probe 1/2).
* **Connection Monitor:** A dedicated sensor tracks whether the thermometer is currently connected or out of range.
* **Hardware Status:** Monitor whether probes are plugged in and if Eco-mode is active.
* **Auto-Discovery:** Home Assistant will automatically detect the device when it is powered on.

## 📦 Installation

### Option 1: Via HACS (Recommended)
As this is a custom integration, you need to add it as a "Custom Repository":

1. Open HACS in Home Assistant.
2. Click the menu (three dots) in the top right corner > **Custom repositories**.
3. Paste the URL of this GitHub repository.
4. Category: **Integration**.
5. Click **Add** and install the integration.
6. **Restart Home Assistant.**

### Option 2: Manual
1. Download the repository.
2. Copy the `custom_components/ooni_connect` folder into your Home Assistant directory under `/config/custom_components/`.
3. Restart Home Assistant.

> **Note:** During the very first restart, Home Assistant will download the required Python library in the background. This restart may take 1–2 minutes longer than usual.

## ⚙️ Configuration

1. Ensure Bluetooth is active on your Home Assistant server (or via ESPHome Proxy).
2. Turn on your Ooni thermometer.
3. Navigate to **Settings > Devices & Services**.
4. The device should either be **automatically discovered**, or:
5. Click **Add Integration** in the bottom right and search for **Ooni Connect**.

## 📊 Available Entities

| Name | Type | Description |
| :--- | :--- | :--- |
| **Ambient Temperature A** | Sensor | Temperature inside the oven (Sensor A) |
| **Ambient Temperature B** | Sensor | Temperature inside the oven (Sensor B) |
| **Probe 1** | Sensor | Core temperature of Probe 1 |
| **Probe 2** | Sensor | Core temperature of Probe 2 |
| **Battery** | Sensor | Charge level in % |
| **Bluetooth Connection** | Binary Sensor | `On` = Connected, `Off` = Not reachable |
| **Probe 1/2 Connected** | Binary Sensor | Indicates if the probe is physically plugged in |
| **Eco Mode** | Binary Sensor | Status of the power-saving mode |

## ❓ Troubleshooting

**Device is not found**
* The Ooni thermometer often allows only **one** active Bluetooth connection. Ensure your phone (Ooni App) is not currently connected to the device.
* Briefly press the power button on the device to wake up the display.

**Sensors are "Unavailable"**
* Check the **"Bluetooth Connection"** sensor. If it is "Off", the device is out of range or turned off.
* "Probe 1/2" sensors will show "Unavailable" if no physical probe is plugged in (verify with the "Probe Connected" sensor).

**Enable Debug Logging**
If you encounter issues, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ooni_connect: debug
