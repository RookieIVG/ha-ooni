# Ooni Connect Bluetooth für Home Assistant

Diese Integration bringt die Daten deines Ooni-Thermometers (oder kompatibler Geräte) direkt in Home Assistant. Sie nutzt Bluetooth Low Energy (BLE), um Temperaturen, Sonden-Status und den Batteriestand in Echtzeit auszulesen.

## Features

* **Automatisches Discovery:** Das Gerät wird automatisch von Home Assistant erkannt, wenn es sich in Bluetooth-Reichweite befindet.
* **Temperatur-Überwachung:** Unterstützung für Umgebungssensoren (Ambient A/B) und Fleischsonden (Probe 1/2).
* **Status-Sensoren:** Überprüfung, ob Sonden eingesteckt sind und ob der Eco-Modus aktiv ist.
* **Batterieanzeige:** Behalte den Ladestand deines Thermometers im Blick.
* **Native Bluetooth Integration:** Nutzt die offizielle Home Assistant Bluetooth-Schnittstelle (kein direkter Zugriff auf `/dev/hci0` nötig).

## Installation

### Manuell
1. Kopiere den Ordner `ooni_connect` aus diesem Repository in deinen `config/custom_components/` Ordner.
2. Starte Home Assistant neu.
3. Gehe zu **Einstellungen > Geräte & Dienste**.
4. Klicke auf **Integration hinzufügen** und suche nach **Ooni Connect Bluetooth**.

### Anforderungen
* Ein funktionierender Bluetooth-Adapter an deinem Home Assistant Host (oder ein Bluetooth-Proxy über ESPHome).

## Unterstützte Entitäten

| Entität | Typ | Beschreibung |
|---------|------|-------------|
| Umgebungstemperatur A/B | Sensor | Misst die Lufttemperatur im Grill/Ofen |
| Sonde 1/2 | Sensor | Kerntermperatur-Messung |
| Sonde 1/2 Verbunden | Binary Sensor | Zeigt an, ob die Sonde physisch eingesteckt ist |
| Batterie | Sensor | Ladestand in Prozent |
| Eco Modus | Binary Sensor | Status der Stromsparfunktion |

## Fehlerbehebung

### Gerät wird nicht gefunden
Stelle sicher, dass:
* Das Ooni-Gerät eingeschaltet ist.
* Das Gerät nicht mit einer anderen App (z.B. auf deinem Handy) verbunden ist, da Bluetooth-Geräte oft nur eine aktive Verbindung gleichzeitig zulassen.
* Dein Home Assistant Bluetooth-Adapter korrekt konfiguriert ist.

## Mitwirkende
* Integration basierend auf der Library von [erwin-willems](https://github.com/erwin-willems/ooni-connect-bluetooth).

---
*Hinweis: Dies ist eine inoffizielle Integration und steht in keiner Verbindung zur Marke Ooni.*
