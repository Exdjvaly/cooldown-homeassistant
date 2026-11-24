"""Messwerte: Leistung, Energie (für das Energie-Dashboard), Temperaturen, SG Ready / §14a (nur lesen)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity, SensorEntityDescription,
                                             SensorStateClass)
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfFrequency, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CooldownConfigEntry
from .const import SG_NAMES
from .entity import CooldownEntity


@dataclass(frozen=True, kw_only=True)
class CdSensor(SensorEntityDescription):
    value: Callable[[dict], Any]
    only_kind: str | None = None


def _s(k: str) -> Callable[[dict], Any]:
    return lambda d: (d.get("sensors") or {}).get(k)


def _hp(k: str) -> Callable[[dict], Any]:
    return lambda d: (d.get("heatpump") or {}).get(k)


TEMP = dict(device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS)

SENSORS: tuple[CdSensor, ...] = (
    CdSensor(key="power_w", translation_key="power_w", value=_s("power_w"), device_class=SensorDeviceClass.POWER,
             state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT),
    CdSensor(key="energy_kwh", translation_key="energy_kwh", value=_s("energy_kwh"),
             device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING,
             native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR),
    CdSensor(key="heat_w", translation_key="heat_w", value=_s("heat_w"), device_class=SensorDeviceClass.POWER,
             state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT),
    CdSensor(key="t_indoor", translation_key="t_indoor", value=_s("t_indoor"), **TEMP),
    CdSensor(key="t_outdoor", translation_key="t_outdoor", value=_s("t_outdoor"), **TEMP),
    CdSensor(key="compressor_hz", translation_key="compressor_hz", value=_s("compressor_hz"),
             device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT,
             native_unit_of_measurement=UnitOfFrequency.HERTZ, entity_category=EntityCategory.DIAGNOSTIC),
    CdSensor(key="sg_state", translation_key="sg_state", device_class=SensorDeviceClass.ENUM,
             options=list(SG_NAMES.values()),
             value=lambda d: SG_NAMES.get((d.get("grid") or {}).get("sg_state") or 2)),
    # §14a: „Keine Begrenzung“ statt „Unbekannt“, wenn der Netzbetreiber nichts vorgibt; die Grenze steht im Attribut.
    CdSensor(key="limit_w", translation_key="limit_w", device_class=SensorDeviceClass.ENUM,
             options=["none", "limited"],
             value=lambda d: "limited" if (d.get("grid") or {}).get("limit_w") else "none"),
    CdSensor(key="t_flow", translation_key="t_flow", value=_hp("t_flow"), only_kind="heatpump", **TEMP),
    CdSensor(key="t_return", translation_key="t_return", value=_hp("t_return"), only_kind="heatpump", **TEMP),
    CdSensor(key="t_dhw", translation_key="t_dhw", value=_hp("t_dhw"), only_kind="heatpump", **TEMP),
)


async def async_setup_entry(hass: HomeAssistant, entry: CooldownConfigEntry,
                            add: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    add(CooldownSensor(c, did, desc) for did, d in c.data.items() for desc in SENSORS
        if desc.only_kind in (None, d.get("kind")))


class CooldownSensor(CooldownEntity, SensorEntity):
    entity_description: CdSensor

    def __init__(self, coordinator, device_id: str, desc: CdSensor) -> None:
        super().__init__(coordinator, device_id, desc.key)
        self.entity_description = desc

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.dev)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "limit_w":
            return None
        g = self.dev.get("grid") or {}
        return {"limit_w": g.get("limit_w") or None, "valid_until": g.get("valid_until")}
