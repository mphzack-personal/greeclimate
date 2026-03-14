"""Constants for the Gree Cloud integration."""

DOMAIN = "greecloud"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_REGION = "region"

# Default region for European server
DEFAULT_REGION = "Europe"

# Gree Cloud servers by region
GREE_CLOUD_SERVERS = {
    "Europe": "https://eugrih.gree.com",
    "East South Asia": "https://hkgrih.gree.com",
    "North American": "https://nagrih.gree.com",
    "South American": "https://sagrih.gree.com",
    "China Mainland": "https://grih.gree.com",
    "India": "https://ingrih.gree.com",
    "Middle East": "https://megrih.gree.com",
    "Australia": "https://augrih.gree.com",
    "Russian server": "https://rugrih.gree.com",
}

# Coordinator update interval
DEFAULT_UPDATE_INTERVAL = 30
