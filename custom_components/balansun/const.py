"""Constants for Balansun integration."""

DOMAIN = "balansun"
CONF_HOST = "host"
CONF_API_TOKEN = "api_token"
CONF_PRODUCT_PROFILE = "product_profile"
PRODUCT_WARM_ACTUATOR = "warm_actuator"
PRODUCT_ACTION_NODE = "action_node"
CONF_INTEGRATION_MODE = "integration_mode"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SKIP_UNAVAILABLE_ON_FAILURE = "skip_unavailable_on_failure"
CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE = "failure_count_until_unavailable"

MODE_COMPANION = "companion"
MODE_REST_ONLY = "rest_only"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 300
DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE = True
DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE = 10
MIN_FAILURE_COUNT_UNTIL_UNAVAILABLE = 0
MAX_FAILURE_COUNT_UNTIL_UNAVAILABLE = 1000

# Brief pause before polling after a REST write (EEPROM / single-threaded HTTP).
POST_WRITE_REFRESH_DELAY_SEC = 0.75
# Source changes re-init metering drivers and EEPROM — allow extra time before poll.
POST_WRITE_SOURCE_DELAY_SEC = 1.5

COMPANION_ENTITY_KEYS = frozenset({"republish_discovery", "self_test_run", "device_reboot"})
