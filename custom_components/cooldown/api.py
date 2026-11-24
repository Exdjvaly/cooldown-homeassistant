"""Kleiner Client für die Cooldown Smart-Home-API (/v1/int/*)."""
from __future__ import annotations

from typing import Any

import aiohttp


class CooldownError(Exception):
    """Allgemeiner Fehler."""


class CooldownAuthError(CooldownError):
    """Token ungültig oder gelöscht (in der App unter Einstellungen → Smart Home)."""


class CooldownApi:
    def __init__(self, session: aiohttp.ClientSession, url: str, token: str | None = None) -> None:
        self._s = session
        self._url = url.rstrip("/")
        self.token = token

    async def _req(self, method: str, path: str, token: str | None = None, **kw: Any) -> Any:
        tok = token or self.token
        headers = {"Authorization": f"Bearer {tok}"} if tok else {}
        try:
            async with self._s.request(method, self._url + path, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=20), **kw) as r:
                if r.status == 401:
                    raise CooldownAuthError("401")
                if r.status >= 400:
                    raise CooldownError(f"{r.status}: {await r.text()}")
                if r.status == 204:
                    return None
                return await r.json()
        except aiohttp.ClientError as e:
            raise CooldownError(str(e)) from e

    async def create_token(self, email: str, password: str, name: str) -> str:
        """Mit App-Konto anmelden, Integrations-Token anlegen, App-Sitzung wieder abmelden.
        Gespeichert wird nur der Integrations-Token, nie das Passwort."""
        login = await self._req("POST", "/v1/auth/login", json={"email": email, "password": password})
        session = login["token"]
        try:
            r = await self._req("POST", "/v1/me/integrations", token=session,
                                json={"name": name, "kind": "homeassistant"})
            return r["token"]
        finally:
            try:
                await self._req("POST", "/v1/auth/logout", token=session)
            except CooldownError:
                pass

    async def devices(self) -> list[dict]:
        return (await self._req("GET", "/v1/int/devices"))["devices"]

    async def command(self, device_id: str, **cmd: Any) -> dict:
        return await self._req("POST", f"/v1/int/devices/{device_id}/cmd", json=cmd)
