import math
import json
from datetime import datetime

import pandas as pd
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


def _serialize_value(v):
    """Convert common non-JSON-native values to serializable forms."""
    try:
        if v is None:
            return None
        if isinstance(v, (str, bool, int, float)):
            return v
        # pandas/numpy types
        try:
            import pandas as _pd
            import numpy as _np

            if isinstance(v, _pd.Timestamp):
                return v.isoformat()
            if isinstance(v, (_np.integer,)):
                return int(v)
            if isinstance(v, (_np.floating,)):
                return float(v)
        except Exception:
            pass
        # fallback to string
        return str(v)
    except Exception:
        return str(v)


gainers_cache = {}
losers_cache = {}
history_cache = {}
news_cache = {}


def _safe_num(x):
    try:
        if x is None:
            return None
        if isinstance(x, (float, int)) and math.isnan(x):
            return None
        return float(x)
    except Exception:
        return None


def _extract_news_item(raw_item: dict) -> dict:
    """Extract and normalize a news item from yfinance response"""
    content = raw_item.get("content", {})
    provider = content.get("provider", {})
    urls = content.get("clickThroughUrl", {})
    thumbnail = content.get("thumbnail", {})
    finance = content.get("finance", {}).get("premiumFinance", {})
    
    thumbnail_urls = {}
    if thumbnail.get("resolutions"):
        for res in thumbnail["resolutions"]:
            tag = res.get("tag", "")
            thumbnail_urls[tag] = res.get("url")
    
    return {
        "id": content.get("id"),
        "title": content.get("title"),
        "summary": content.get("summary"),
        "datePublished": content.get("pubDate"),
        "provider": {
            "name": provider.get("displayName"),
            "url": provider.get("url"),
        },
        "articleUrl": urls.get("url") if urls else None,
        "thumbnail": thumbnail.get("originalUrl"),
        "thumbnails": thumbnail_urls,
        "isPremium": finance.get("isPremiumNews", False),
        "isEditorsPick": content.get("metadata", {}).get("editorsPick", False),
    }


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


@app.get("/stocks/{ticker}/history")
def api_stock_history(ticker: str, period: str = "1mo", interval: str = "1d", limit: int = None):
    """Return OHLCV history for a ticker (suitable for charting).

    - `period`: e.g. 1mo, 3mo, 1y
    - `interval`: e.g. 1d, 1wk, 1mo, 60m
    - `limit`: optional cap on number of returned records (latest N)
    """
    cache_key = f"history_{ticker}_{period}_{interval}_{limit}"

    if cache_key in history_cache and is_cache_valid(cache_key):
        cached = history_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if not ticker:
            return {"error": "ticker is required", "status": "failed"}

        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)

        # Use pandas to_json then json.loads to get a Python list of records
        # This returns values as JSON-native types (dates as ISO strings).
        if isinstance(hist, pd.DataFrame) and not hist.empty:
            df = hist.reset_index()
            if limit is not None and isinstance(limit, int) and limit > 0:
                df = df.tail(limit)
            history_json = df.to_json(orient="records", date_format="iso")
            history = json.loads(history_json)
            count = len(history)
        else:
            history = []
            count = 0

        response = {
            "ticker": ticker,
            "history": history,
            "count": count,
            "period": period,
            "interval": interval,
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }

        history_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response

    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


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


@app.get("/stocks/{ticker}")
def api_stock_detail(ticker: str, period: str = "1mo", interval: str = "1d"):
    """
    Stock detail endpoint

    Parameters:
    - ticker: Stock ticker (e.g. BBCA.JK)
    - period: History period (e.g. 1mo, 3mo, 1y)
    - interval: Data interval (e.g. 1d, 1wk, 1mo)

    Returns a JSON with company info and OHLCV history.
    """
    try:
        if not ticker:
            return {"error": "ticker is required", "status": "failed"}

        t = yf.Ticker(ticker)

        try:
            raw_info = t.info or {}
        except Exception:
            raw_info = {}

        # serialized full raw_info for return
        serialized_raw = {k: _serialize_value(v) for k, v in raw_info.items()} if isinstance(raw_info, dict) else {}

        return {
            "ticker": ticker,
            "raw_info": serialized_raw,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/stocks/{ticker}/news")
def api_stock_news(ticker: str, count: int = 10, tab: str = "all"):
    """
    Get news feed for a stock ticker

    Parameters:
    - ticker: Stock ticker (e.g., AAPL, BBCA.JK)
    - count: Number of news items (default: 10, max: 50)
    - tab: News type - 'news' (default), 'all', or 'press releases'

    Returns: {"news": [...news items...], "count": 10, "ticker": "AAPL"}
    """
    cache_key = f"news_{ticker}_{count}_{tab}"

    if cache_key in news_cache and is_cache_valid(cache_key, ttl_seconds=1800):
        cached_response = news_cache[cache_key].copy()
        cached_response["cached"] = True
        return cached_response

    try:
        if count > 50:
            count = 50
        if tab not in ["news", "all", "press releases"]:
            tab = "news"

        t = yf.Ticker(ticker)
        raw_news = t.get_news(count=count, tab=tab)

        if not raw_news:
            response = {
                "news": [],
                "count": 0,
                "ticker": ticker,
                "newsType": tab,
                "message": "No news available for this ticker",
                "timestamp": datetime.now().isoformat(),
                "cached": False,
            }
            news_cache[cache_key] = response
            cache_timestamps[cache_key] = datetime.now()
            return response

        news = [_extract_news_item(item) for item in raw_news]

        response = {
            "news": news,
            "count": len(news),
            "ticker": ticker,
            "newsType": tab,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        news_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

