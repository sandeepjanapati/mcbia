import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    WORK_ORDERS_BOARD_ID = os.getenv("WORK_ORDERS_BOARD_ID")
    DEALS_BOARD_ID = os.getenv("DEALS_BOARD_ID")
    MONDAY_URL = "https://api.monday.com/v2"
    MONDAY_API_VERSION = "2026-01"

    @staticmethod
    def validate():
        required = {
            "MONDAY_API_KEY": Config.MONDAY_API_KEY,
            "GOOGLE_API_KEY": Config.GOOGLE_API_KEY,
            "WORK_ORDERS_BOARD_ID": Config.WORK_ORDERS_BOARD_ID,
            "DEALS_BOARD_ID": Config.DEALS_BOARD_ID,
        }
        missing = [name for name, val in required.items() if not val]
        if missing:
            raise ValueError(f"❌ Missing in .env: {', '.join(missing)}")
        return True

    @staticmethod
    def summary():
        return {
            "monday_url": Config.MONDAY_URL,
            "api_version": Config.MONDAY_API_VERSION,
            "work_orders_board": Config.WORK_ORDERS_BOARD_ID,
            "deals_board": Config.DEALS_BOARD_ID,
            "api_key_set": bool(Config.MONDAY_API_KEY),
            "google_key_set": bool(Config.GOOGLE_API_KEY),
        }