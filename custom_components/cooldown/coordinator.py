"""Fragt alle Geräte des Kontos alle 30 s in einem einzigen Aufruf ab."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CooldownApi, CooldownAuthError, CooldownError
from .const import DOMAIN, SCAN_INTERVAL_S

_LOGGER = logging.getLogger(__name__)


class CooldownCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: CooldownApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=timedelta(seconds=SCAN_INTERVAL_S))
        self.api = api

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            return {d["device_id"]: d for d in await self.api.devices()}
        except CooldownAuthError as e:
            raise ConfigEntryAuthFailed("Token ungültig") from e
        except CooldownError as e:
            raise UpdateFailed(str(e)) from e
