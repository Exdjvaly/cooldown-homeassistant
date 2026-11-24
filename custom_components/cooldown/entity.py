"""Gemeinsame Basis: ein Gerät in HA pro Cooldown-Stick."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import CooldownCoordinator


class CooldownEntity(CoordinatorEntity[CooldownCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: CooldownCoordinator, device_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"
        d = self.dev
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)}, name=d.get("name") or device_id, manufacturer=MANUFACTURER,
            model=d.get("model") or ("Wärmepumpe" if d.get("kind") == "heatpump" else "Klimagerät"),
            sw_version=d.get("fw"), serial_number=device_id)

    @property
    def dev(self) -> dict:
        return self.coordinator.data.get(self.device_id, {})

    @property
    def available(self) -> bool:
        return super().available and self.device_id in self.coordinator.data
