# Cooldown für Home Assistant

Klimageräte mit **Cooldown-Stick** in Home Assistant: Thermostat, Leistung, Energie (für das Energie-Dashboard),
Raum- und Außentemperatur, SG Ready und die §14a-Grenze. Die Verbindung läuft über den Cooldown-Server
(Internet nötig), am Stick muss nichts geändert werden.

## Installation über HACS
1. HACS öffnen → oben rechts **⋮** → **Benutzerdefinierte Repositories**
2. Repository: `https://github.com/Exdjvaly/cooldown-homeassistant`, Typ: **Integration** → Hinzufügen
3. In HACS nach **Cooldown** suchen → **Herunterladen**
4. Home Assistant neu starten
5. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → **Cooldown**
6. E-Mail und Passwort der **Cooldown-App** eingeben – fertig

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Exdjvaly&repository=cooldown-homeassistant&category=integration)

Das Passwort wird nicht gespeichert. Home Assistant bekommt einen eigenen Zugang, der in der App unter
**Einstellungen → Smart Home** erscheint und dort jederzeit gelöscht werden kann.

## Was erscheint
| Entität | Bedeutung |
|---|---|
| Klima (Thermostat) | Aus, Auto, Kühlen, Heizen, Entfeuchten, Lüften · Sollwert 16–30 °C · Lüfter, Preset, Swing |
| Leistung | elektrische Leistung (W) |
| Energie | Zählerstand (kWh), fürs Energie-Dashboard |
| Raumtemperatur, Außentemperatur | °C |
| SG Ready | Gesperrt / Normal / Empfohlen / Erzwungen (nur lesen) |
| Leistungsgrenze §14a | W (nur lesen) |
| Verbindung | Stick mit dem Server verbunden |

Werte werden alle 30 Sekunden aktualisiert. Sperren des Netzbetreibers (SG Ready, §14a) gelten immer,
auch wenn eine Automation etwas anderes schickt.

---

## English
Air conditioners with a **Cooldown stick** in Home Assistant (climate, power, energy, temperatures, SG Ready).
Install via HACS (custom repository above, category *Integration*), restart, then add the **Cooldown** integration
and sign in with your Cooldown app account. Cloud polling, 30 s.

Cooldown Solution GmbH i. G. · https://cooldown-solution.de
