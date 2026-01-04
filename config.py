"""Configuration module for Freelancehunt auto-bid bot."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8369104694:AAEWBhegpsS_O0K175jYA8CgE6bJwq4uA1w")

# Freelancehunt Configuration
FREELANCEHUNT_URL = os.getenv("FREELANCEHUNT_URL", "https://freelancehunt.com")
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.json")

# Database Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "freelancehunt_bot.db")

# Bot Settings
MAX_BID_AMOUNT = int(os.getenv("MAX_BID_AMOUNT", "27000"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # seconds
DEFAULT_CATEGORIES = os.getenv("DEFAULT_CATEGORIES", "").split(",") if os.getenv("DEFAULT_CATEGORIES") else []

# Security
ALLOWED_USER_IDS = [
    int(uid.strip()) 
    for uid in os.getenv("ALLOWED_USER_IDS", "1797952290,5796191806").split(",")  # Default user IDs
    if uid.strip()
]

# Paths
BASE_DIR = Path(__file__).parent
# Use /app/data for Render persistent disk, fallback to local directory
# Check if /app/data exists (Render persistent disk) or use BASE_DIR
DATA_DIR = Path("/app/data")
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR
    # Try to create /app/data if we're in Docker but it doesn't exist yet
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except:
        pass

COOKIES_PATH = DATA_DIR / COOKIES_FILE
DATABASE_PATH = DATA_DIR / DATABASE_FILE

# Browser Configuration
HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chrome")  # chrome or edge (chrome works better on Linux servers)

