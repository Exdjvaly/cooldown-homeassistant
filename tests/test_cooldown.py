"""Teste cu Home Assistant real (pytest-homeassistant-custom-component), serverul Cooldown e simulat."""
from homeassistant import config_entries
from homeassistant.components.climate import HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cooldown.const import DOMAIN

URL = "https://api.cooldown-solution.de"
DEV = {"device_id": "cd-8c4f0051fe3e", "name": "Lounge", "kind": "ac", "model": "Vivax Y", "fw": "1.0.0",
       "online": True, "state": {"power": True, "mode": "heat", "setpoint": 22, "fan": "auto", "preset": "none",
                                 "swing": "off"},
       "sensors": {"t_indoor": 21.5, "t_outdoor": 4.0, "power_w": 410.0, "energy_kwh": 123.456, "heat_w": 1500.0,
                   "compressor_hz": 42.0},
       "grid": {"sg_state": 1, "limit_w": 4200}}


async def test_config_flow(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(f"{URL}/v1/auth/login", json={"token": "sess"})
    aioclient_mock.post(f"{URL}/v1/me/integrations", json={"token": "cdi_abc"})
    aioclient_mock.post(f"{URL}/v1/auth/logout", status=204)
    aioclient_mock.get(f"{URL}/v1/int/devices", json={"devices": [DEV]})
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.FORM
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"email": "A@b.de", "password": "geheim12345"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["data"]["token"] == "cdi_abc" and "password" not in r["data"]
    # sesiunea din aplicație a fost închisă după ce s-a făcut tokenul
    assert any(str(c[1]).endswith("/v1/auth/logout") for c in aioclient_mock.mock_calls)


async def test_config_flow_wrong_password(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(f"{URL}/v1/auth/login", status=401)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"email": "a@b.de", "password": "x"})
    assert r["type"] is FlowResultType.FORM and r["errors"] == {"base": "invalid_auth"}


async def setup(hass, aioclient_mock):
    aioclient_mock.get(f"{URL}/v1/int/devices", json={"devices": [DEV]})
    entry = MockConfigEntry(domain=DOMAIN, unique_id="a@b.de", data={"url": URL, "token": "cdi_abc"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_entities(hass: HomeAssistant, aioclient_mock):
    await setup(hass, aioclient_mock)
    c = hass.states.get("climate.lounge")
    assert c.state == HVACMode.HEAT and c.attributes["temperature"] == 22
    assert c.attributes["current_temperature"] == 21.5 and c.attributes["sg_ready"] == "gesperrt"
    e = hass.states.get("sensor.lounge_energy")
    assert float(e.state) == 123.456 and e.attributes["state_class"] == "total_increasing"
    assert hass.states.get("sensor.lounge_sg_ready").state == "gesperrt"
    assert hass.states.get("binary_sensor.lounge_connection").state == "on"


async def test_command(hass: HomeAssistant, aioclient_mock):
    await setup(hass, aioclient_mock)
    aioclient_mock.post(f"{URL}/v1/int/devices/cd-8c4f0051fe3e/cmd", json={"id": 7, "status": "sent"})
    await hass.services.async_call("climate", "set_temperature",
                                   {"entity_id": "climate.lounge", "temperature": 23.3}, blocking=True)
    await hass.services.async_call("climate", "set_hvac_mode",
                                   {"entity_id": "climate.lounge", "hvac_mode": "off"}, blocking=True)
    sent = [c[2] for c in aioclient_mock.mock_calls if str(c[1]).endswith("/cmd")]
    assert sent == [{"setpoint": 23.5}, {"power": False}]
    assert hass.states.get("climate.lounge").state == HVACMode.OFF


async def test_bad_token_starts_reauth(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.get(f"{URL}/v1/int/devices", status=401)
    entry = MockConfigEntry(domain=DOMAIN, unique_id="a@b.de", data={"url": URL, "token": "cdi_old"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    assert any(f["context"]["source"] == "reauth" for f in hass.config_entries.flow.async_progress())
