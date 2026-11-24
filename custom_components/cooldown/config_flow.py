"""Einrichtung: mit dem Konto aus der Cooldown-App anmelden. Gespeichert wird nur ein Integrations-Token."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CooldownApi, CooldownAuthError, CooldownError
from .const import CONF_TOKEN, CONF_URL, DEFAULT_URL, DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str})


class CooldownConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _token(self, user_input: dict[str, Any], errors: dict[str, str]) -> str | None:
        api = CooldownApi(async_get_clientsession(self.hass), DEFAULT_URL)
        try:
            return await api.create_token(user_input[CONF_EMAIL].strip(), user_input[CONF_PASSWORD],
                                          f"Home Assistant ({self.hass.config.location_name})"[:40])
        except CooldownAuthError:
            errors["base"] = "invalid_auth"
        except CooldownError:
            errors["base"] = "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()
            if tok := await self._token(user_input, errors):
                return self.async_create_entry(title=email, data={CONF_URL: DEFAULT_URL, CONF_TOKEN: tok})
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and (tok := await self._token(user_input, errors)):
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates={CONF_TOKEN: tok})
        return self.async_show_form(step_id="reauth_confirm", data_schema=SCHEMA, errors=errors)
