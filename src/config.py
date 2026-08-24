from pathlib import Path
import os


from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT/"Data"
LOG_DIR = PROJECT_ROOT/"log"

API_KEY = os.getenv("OPENAQ_API_KEY")

HEADER_JSON = {
    "X-API-Key": API_KEY
}

BASE_URL = "https://api.openaq.org/v3"

DB_HOST = os.getenv("DB_HOST")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
