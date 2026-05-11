import os
import finnhub
from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5000",
    "https://yourdomain.com",
]

finnhub_api_key = os.getenv("FINNHUB_API_KEY")
if not finnhub_api_key:
    raise ValueError("FINNHUB_API_KEY environment variable is required")

finnhub_client = finnhub.Client(api_key=finnhub_api_key)

YAHOO_SECTORS = [
    {"name": "Financial Services", "key": "financial-services", "displayName": "FINANCIAL"},
    {"name": "Energy", "key": "energy", "displayName": "ENERGY"},
    {"name": "Technology", "key": "technology", "displayName": "TECHNOLOGY"},
    {"name": "Basic Materials", "key": "basic-materials", "displayName": "MATERIAL"},
    {"name": "Consumer Cyclical", "key": "consumer-cyclical", "displayName": "CYCLICAL"},
    {"name": "Consumer Defensive", "key": "consumer-defensive", "displayName": "NON-CYCLICAL"},
    {"name": "Healthcare", "key": "healthcare", "displayName": "HEALTH"},
    {"name": "Industrials", "key": "industrials", "displayName": "INDUSTRIAL"},
    {"name": "Real Estate", "key": "real-estate", "displayName": "PROPERTY"},
    {"name": "Utilities", "key": "utilities", "displayName": "UTILITY"},
    {"name": "Communication Services", "key": "communication-services", "displayName": "TELECOM"},
]

SECTOR_KEY_MAP = {s["key"]: s for s in YAHOO_SECTORS}

SUPPORTED_INDICES = ["^JKSE", "^GSPC", "^DJI", "^IXIC", "^N225", "^HSI", "^BVSP", "^FTSE", "^FCHI", "^GDAXI"]

INDEX_INFO_MAP = {
    "^JKSE": {"name": "IDX Composite", "country": "Indonesia", "currency": "IDR"},
    "^GSPC": {"name": "S&P 500", "country": "USA", "currency": "USD"},
    "^DJI": {"name": "Dow Jones Industrial Average", "country": "USA", "currency": "USD"},
    "^IXIC": {"name": "NASDAQ Composite", "country": "USA", "currency": "USD"},
    "^N225": {"name": "Nikkei 225", "country": "Japan", "currency": "JPY"},
    "^HSI": {"name": "Hang Seng Index", "country": "Hong Kong", "currency": "HKD"},
    "^BVSP": {"name": "Bovespa", "country": "Brazil", "currency": "BRL"},
    "^FTSE": {"name": "FTSE 100", "country": "UK", "currency": "GBP"},
    "^FCHI": {"name": "CAC 40", "country": "France", "currency": "EUR"},
    "^GDAXI": {"name": "DAX", "country": "Germany", "currency": "EUR"},
}

