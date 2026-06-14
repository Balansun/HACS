"""Options flow for integration mode and poll interval."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    CONF_INTEGRATION_MODE,
    CONF_SCAN_INTERVAL,
    CONF_SKIP_UNAVAILABLE_ON_FAILURE,
    DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE,
    MAX_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    MAX_SCAN_INTERVAL,
    MIN_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    MIN_SCAN_INTERVAL,
    MODE_COMPANION,
    MODE_REST_ONLY,
)


class BalansunOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_INTEGRATION_MODE,
                        default=entry.options.get(CONF_INTEGRATION_MODE, MODE_REST_ONLY),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[MODE_REST_ONLY, MODE_COMPANION],
                            translation_key="integration_mode",
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
                    vol.Optional(
                        CONF_SKIP_UNAVAILABLE_ON_FAILURE,
                        default=entry.options.get(
                            CONF_SKIP_UNAVAILABLE_ON_FAILURE,
                            DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE,
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
                        default=entry.options.get(
                            CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
                            DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_FAILURE_COUNT_UNTIL_UNAVAILABLE,
                            max=MAX_FAILURE_COUNT_UNTIL_UNAVAILABLE,
                        ),
                    ),
                }
            ),
        )
