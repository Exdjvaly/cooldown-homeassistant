"""Cooldown: Klimageräte mit Cooldown-Stick in Home Assistant (über den Cooldown-Server)."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CooldownApi
from .const import CONF_TOKEN, CONF_URL, DEFAULT_URL
from .coordinator import CooldownCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR]

type CooldownConfigEntry = ConfigEntry[CooldownCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CooldownConfigEntry) -> bool:
    api = CooldownApi(async_get_clientsession(hass), entry.data.get(CONF_URL, DEFAULT_URL), entry.data[CONF_TOKEN])
    coordinator = CooldownCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CooldownConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
