"""Klimagerät als Thermostat. Wärmepumpen (kind = heatpump) erscheinen nur mit Sensoren."""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CooldownConfigEntry
from .api import CooldownError
from .const import SG_NAMES
from .entity import CooldownEntity

MODES = {"auto": HVACMode.AUTO, "cool": HVACMode.COOL, "heat": HVACMode.HEAT, "dry": HVACMode.DRY,
         "fan_only": HVACMode.FAN_ONLY}
MODES_INV = {v: k for k, v in MODES.items()}
FANS = ["auto", "silent", "low", "medium", "high", "turbo"]
PRESETS = ["none", "eco", "boost", "sleep", "frost"]
SWINGS = ["off", "vertical", "horizontal", "both"]


async def async_setup_entry(hass: HomeAssistant, entry: CooldownConfigEntry,
                            add: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    add(CooldownClimate(c, did) for did, d in c.data.items() if d.get("kind") != "heatpump")


class CooldownClimate(CooldownEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.OFF, *MODES.values()]
    _attr_fan_modes = FANS
    _attr_preset_modes = PRESETS
    _attr_swing_modes = SWINGS
    _attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
                                | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.SWING_MODE
                                | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF)

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "climate")

    @property
    def available(self) -> bool:
        return super().available and bool(self.dev.get("online"))

    @property
    def _st(self) -> dict:
        return self.dev.get("state") or {}

    @property
    def hvac_mode(self) -> HVACMode:
        if not self._st.get("power"):
            return HVACMode.OFF
        return MODES.get(self._st.get("mode") or "auto", HVACMode.AUTO)

    @property
    def current_temperature(self) -> float | None:
        return (self.dev.get("sensors") or {}).get("t_indoor")

    @property
    def target_temperature(self) -> float | None:
        return self._st.get("setpoint")

    @property
    def fan_mode(self) -> str | None:
        return self._st.get("fan")

    @property
    def preset_mode(self) -> str | None:
        return self._st.get("preset")

    @property
    def swing_mode(self) -> str | None:
        return self._st.get("swing")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        g = self.dev.get("grid") or {}
        return {"sg_ready": SG_NAMES.get(g.get("sg_state"), g.get("sg_state")), "limit_w": g.get("limit_w"),
                "setpoint_active": self._st.get("setpoint_active")}

    async def _send(self, **cmd: Any) -> None:
        try:
            await self.coordinator.api.command(self.device_id, **cmd)
        except CooldownError as e:
            raise HomeAssistantError(f"Cooldown: {e}") from e
        # sofort anzeigen, dann nach kurzer Zeit die echte Rückmeldung des Sticks holen
        self.dev.setdefault("state", {}).update(cmd)
        self.async_write_ha_state()
        self.hass.async_create_background_task(self._refresh_later(), "cooldown_refresh")

    async def _refresh_later(self) -> None:
        await asyncio.sleep(3)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._send(power=False)
        else:
            await self._send(power=True, mode=MODES_INV[hvac_mode])

    async def async_turn_on(self) -> None:
        await self._send(power=True)

    async def async_turn_off(self) -> None:
        await self._send(power=False)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        cmd: dict[str, Any] = {}
        if (t := kwargs.get(ATTR_TEMPERATURE)) is not None:
            cmd["setpoint"] = round(float(t) * 2) / 2
        if (m := kwargs.get("hvac_mode")) is not None:
            cmd.update({"power": False} if m == HVACMode.OFF else {"power": True, "mode": MODES_INV[m]})
        if cmd:
            await self._send(**cmd)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._send(fan=fan_mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._send(preset=preset_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._send(swing=swing_mode)
