# Ooni Connect Bluetooth für Home Assistant

![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

Eine Home Assistant Integration für das **Ooni Digital Thermometer** (bekannt vom Ooni Karu 16 und separat erhältlich). Diese Integration liest die Temperaturen, den Batteriestand und den Status der Sonden direkt über Bluetooth Low Energy (BLE) aus.

## ✨ Features

* **Echtzeit-Temperaturen:** Auslesen der Umgebungssensoren (Ambient A/B) und der Fleischsonden (Probe 1/2).
* **Verbindungs-Monitor:** Ein eigener Sensor zeigt an, ob das Thermometer aktuell verbunden ist oder die Reichweite verlassen hat.
* **Hardware-Status:** Überwacht, ob Sonden eingesteckt sind und ob der Eco-Modus aktiv ist.
* **Auto-Discovery:** Home Assistant findet das Gerät automatisch, wenn es eingeschaltet ist.

## 📦 Installation

### Option 1: Via HACS (Empfohlen)
Da dies eine benutzerdefinierte Integration ist, musst du sie als "Custom Repository" hinzufügen:

1.  Öffne HACS in Home Assistant.
2.  Gehe oben rechts auf das Menü (drei Punkte) > **Benutzerdefinierte Repositories**.
3.  Füge die URL dieses GitHub-Repositories ein.
4.  Kategorie: **Integration**.
5.  Klicke auf **Hinzufügen** und installiere die Integration.
6.  **Starte Home Assistant neu.**

### Option 2: Manuell
1.  Lade das Repository herunter.
2.  Kopiere den Ordner `custom_components/ooni_connect` in dein Home Assistant Verzeichnis unter `/config/custom_components/`.
3.  Starte Home Assistant neu.

> **Wichtig:** Beim allerersten Neustart lädt Home Assistant die benötigte Python-Library im Hintergrund herunter. Dieser Neustart kann 1–2 Minuten länger dauern als gewöhnlich.

## ⚙️ Konfiguration

1.  Stelle sicher, dass Bluetooth auf deinem Home Assistant Server (oder via ESPHome Proxy) aktiv ist.
2.  Schalte dein Ooni Thermometer ein.
3.  Gehe zu **Einstellungen > Geräte & Dienste**.
4.  Entweder wird das Gerät dort bereits **automatisch entdeckt**, oder:
5.  Klicke unten rechts auf **Integration hinzufügen** und suche nach **Ooni Connect**.

## 📊 Verfügbare Entitäten

| Name | Typ | Beschreibung |
| :--- | :--- | :--- |
| **Umgebungstemperatur A** | Sensor | Temperatur im Ofen (Sensor A) |
| **Umgebungstemperatur B** | Sensor | Temperatur im Ofen (Sensor B) |
| **Sonde 1** | Sensor | Kerntemperatur Sonde 1 |
| **Sonde 2** | Sensor | Kerntemperatur Sonde 2 |
| **Batterie** | Sensor | Ladestand in % |
| **Bluetooth Verbindung** | Binary Sensor | `An` = Verbunden, `Aus` = Nicht erreichbar |
| **Sonde 1/2 Verbunden** | Binary Sensor | Zeigt an, ob die Sonde physisch eingesteckt ist |
| **Eco Modus** | Binary Sensor | Status des Stromsparmodus |

## ❓ Fehlerbehebung

**Das Gerät wird nicht gefunden**
* Das Ooni Thermometer erlaubt oft nur **eine** aktive Bluetooth-Verbindung. Stelle sicher, dass dein Handy (Ooni App) nicht gerade verbunden ist.
* Drücke kurz den Power-Knopf am Gerät, um das Display zu aktivieren.

**Sensoren sind "Nicht verfügbar"**
* Prüfe den Sensor **"Bluetooth Verbindung"**. Wenn dieser auf "Aus" steht, ist das Gerät außer Reichweite oder ausgeschaltet.
* Der Sensor "Sonde 1/2" wird "Nicht verfügbar" anzeigen, wenn physikalisch keine Sonde eingesteckt ist (siehe "Sonde Verbunden" Sensor).

**Debug Logging aktivieren**
Falls Probleme auftreten, füge dies in deine `configuration.yaml` ein:

```yaml
logger:
  default: info
  logs:
    custom_components.ooni_connect: debug
