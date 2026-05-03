from datetime import datetime, timedelta
from functools import lru_cache

import uvicorn
import yfinance as yf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from yfinance import EquityQuery

app = FastAPI(title="Yahoo Finance API", version="0.1.0")

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5000",
    "https://yourdomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache_timestamps = {}


@app.get("/health")
def health_check():
    """
    Health check endpoint
    Returns: {"status": "ok", "timestamp": "2024-05-03T10:30:00"}
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Yahoo Finance API",
        "version": "0.1.0",
    }


def is_cache_valid(key: str, ttl_seconds: int = 300) -> bool:
    """Check if cached data is still valid (TTL: 5 minutes by default)"""
    if key not in cache_timestamps:
        return False
    elapsed = (datetime.now() - cache_timestamps[key]).total_seconds()
    return elapsed < ttl_seconds


gainers_cache = {}
losers_cache = {}


@app.get("/stocks/gainers")
def api_gainers(limit: int = 10, region: str = "id"):
    """
    Get top daily gainers from Indonesia stock market

    Parameters:
    - limit: Number of stocks to return (default: 10, max: 50)
    - region: Stock market region (default: "id" for Indonesia)

    Returns: {"stocks": [...], "count": 10, "region": "id"}
    """
    cache_key = f"gainers_{region}_{limit}"

    if cache_key in gainers_cache and is_cache_valid(cache_key):
        cached_response = gainers_cache[cache_key].copy()
        cached_response["cached"] = True
        return cached_response

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('gt', ['percentchange', 0]),
        ])

        result = yf.screen(
            query,
            sortField='percentchange',
            sortAsc=False,
            size=limit
        )

        quotes = result.get('quotes', [])

        stocks = []
        for q in quotes:
            stocks.append({
                "ticker": q.get("symbol", "N/A"),
                "name": q.get("shortName", "N/A"),
                "price": q.get("regularMarketPrice", 0),
                "change_percent": round(q.get("regularMarketChangePercent", 0), 2),
                "volume": q.get("regularMarketVolume", 0),
                "market_cap": q.get("marketCap", 0),
            })

        response = {
            "stocks": stocks,
            "count": len(stocks),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        gainers_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/stocks/losers")
def api_losers(limit: int = 10, region: str = "id"):
    """
    Get top daily losers from Indonesia stock market

    Parameters:
    - limit: Number of stocks to return (default: 10, max: 50)
    - region: Stock market region (default: "id" for Indonesia)

    Returns: {"stocks": [...], "count": 10, "region": "id"}
    """
    cache_key = f"losers_{region}_{limit}"

    if cache_key in losers_cache and is_cache_valid(cache_key):
        cached_response = losers_cache[cache_key].copy()
        cached_response["cached"] = True
        return cached_response

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('lt', ['percentchange', 0]),
        ])

        result = yf.screen(
            query,
            sortField='percentchange',
            sortAsc=True,
            size=limit
        )

        quotes = result.get('quotes', [])

        stocks = []
        for q in quotes:
            stocks.append({
                "ticker": q.get("symbol", "N/A"),
                "name": q.get("shortName", "N/A"),
                "price": q.get("regularMarketPrice", 0),
                "change_percent": round(q.get("regularMarketChangePercent", 0), 2),
                "volume": q.get("regularMarketVolume", 0),
                "market_cap": q.get("marketCap", 0),
            })

        response = {
            "stocks": stocks,
            "count": len(stocks),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        losers_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

