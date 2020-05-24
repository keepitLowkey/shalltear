# Version
CURRENT_VERSION = "v0.0.2b"

# Command prefix
COMMAND_PREFIX = "==="

# Location of secrets.json where the discord bot token is located.
SECRETS_FILE = "secrets.json"

# Location of resources
ASSETS_DIRECTORY = "assets/"
BACKUP_DIRECTORY = "backup/"

# Logging format
LOGGING_FORMAT = "(%(asctime)s) [%(levelname)s] - %(message)s"

# Cogs in use
ACTIVE_COGS = [
    "cogs.admin",
    "cogs.core",
    "cogs.economy",
    "cogs.farm",
    "cogs.progression",
]

ACTIVE_OBJECTS = [
    "objects.core.profile",
    "objects.economy.core.account",
    "objects.economy.core.transaction",
    "objects.economy.farm.farm",
    "objects.economy.farm.harvest",
    "objects.economy.farm.plot",
    "objects.economy.farm.plant",
]

ACTIVE_SEEDERS = [
    "objects.economy.farm.seeders.plant",
]

# Core
BASE_EXPERIENCE = 100
EXP_FACTOR = 1.2
EXP_PER_MESSAGE = 1
LEVEL_UP_MATERIA_REWARD = 1

# Economy
TRANSFER_TAX = 0.01

# Farms
PLANT_PRICE_GRAPH_DIRECTORY = ASSETS_DIRECTORY+"graphs/plant_prices/"
BASE_PLOT_PRICE = 500000
PLOT_PRICE_FACTOR = 1.45
BASE_STORAGE_UPGRADE_PRICE = 500000
STORAGE_UPGRADE_PRICE_FACTOR = 1.1
FARM_NAME_CHANGE_PRICE = 1000000
FARM_PLOTS_MAX = 1000
DEMAND_DIVISOR = 2.5
MARKET_TOLERANCE = 0.90
