"""Config flow for Balansun."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .connection import async_fetch_product_profile, async_validate_router, normalize_host, resolve_api_token
from .const import CONF_API_TOKEN, CONF_PRODUCT_PROFILE, DOMAIN, PRODUCT_ACTION_NODE, PRODUCT_WARM_ACTUATOR
from .device_info import title_from_public


def _connection_schema(
    *,
    default_host: str,
    default_token: str = "",
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=default_host): str,
            vol.Optional(CONF_API_TOKEN, default=default_token): str,
        }
    )


class BalansunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        from .options_flow import BalansunOptionsFlow

        return BalansunOptionsFlow()

    async def _async_try_connect(
        self,
        user_input: dict[str, Any],
        *,
        reconfigure_entry: config_entries.ConfigEntry | None,
    ) -> tuple[dict[str, Any] | None, str | None, str, str | None]:
        """Return (public_body, error_key, normalized_host, token_to_store)."""
        try:
            host = normalize_host(user_input[CONF_HOST])
        except ValueError:
            return None, "cannot_connect", "", None

        existing = None
        if reconfigure_entry is not None:
            existing = reconfigure_entry.data.get(CONF_API_TOKEN) or None
        token = resolve_api_token(
            user_input.get(CONF_API_TOKEN),
            existing_token=existing,
            reconfigure=reconfigure_entry is not None,
        )

        session = async_get_clientsession(self.hass)
        body, err = await async_validate_router(session, host, token)
        if err:
            return None, err, host, token
        return body, None, host, token

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        default_host = "http://192.168.1.42"
        if user_input is not None:
            body, err, host, token = await self._async_try_connect(user_input, reconfigure_entry=None)
            if err:
                errors["base"] = err
                default_host = user_input.get(CONF_HOST, default_host)
            else:
                assert body is not None
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                session = async_get_clientsession(self.hass)
                product_profile = await async_fetch_product_profile(session, host, token)
                return self.async_create_entry(
                    title=title_from_public(body, host),
                    data={
                        CONF_HOST: host,
                        CONF_API_TOKEN: token or "",
                        CONF_PRODUCT_PROFILE: product_profile or "",
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(
                default_host=user_input.get(CONF_HOST, default_host) if user_input else default_host,
                default_token=(user_input.get(CONF_API_TOKEN, "") if user_input else ""),
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        default_host = reconfigure_entry.data[CONF_HOST]
        if user_input is not None:
            body, err, host, token = await self._async_try_connect(
                user_input, reconfigure_entry=reconfigure_entry
            )
            if err:
                errors["base"] = err
                default_host = user_input.get(CONF_HOST, default_host)
            else:
                assert body is not None
                try:
                    current_host = normalize_host(reconfigure_entry.data[CONF_HOST])
                except ValueError:
                    current_host = ""
                if host != current_host:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    unique_id=host,
                    data={CONF_HOST: host, CONF_API_TOKEN: token or ""},
                    title=title_from_public(body, host),
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(
                default_host=user_input.get(CONF_HOST, default_host) if user_input else default_host,
                default_token=(user_input.get(CONF_API_TOKEN, "") if user_input else ""),
            ),
            errors=errors,
        )
