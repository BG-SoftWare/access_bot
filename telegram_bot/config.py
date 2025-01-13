import os

from dotenv import load_dotenv

if ".env" in os.listdir("."):
    load_dotenv(".env")

LISTEN_HOST = os.getenv("LISTEN_HOST", "0.0.0.0") if not os.getenv("DOCKERIZED", "0") == "1" else "0.0.0.0"
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "9000"))
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
DB_CONNECTION_STRING = f"sqlite+aiosqlite:///{os.path.dirname(os.path.abspath(__file__))}/data/database.sqlite"
REDIS_CONNECTION_STRING = f"redis://:{os.getenv('REDIS_PASS')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}"
APPS_ON_PAGE = 10
APP_ID_HEADER = os.getenv("APP_ID_HEADER", "APP_ID")
OK_RESPONSE = os.getenv("OK_RESPONSE", "OK")
BLOCKED_RESPONSE = os.getenv("BLOCKED_RESPONSE", "BLOCKED")
