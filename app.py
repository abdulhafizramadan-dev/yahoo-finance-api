import math
import json
import os
from datetime import datetime

import pandas as pd
import uvicorn
import yfinance as yf
import finnhub
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from yfinance import EquityQuery
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Yahoo Finance API", version="0.1.0")

finnhub_api_key = os.getenv("FINNHUB_API_KEY")
if not finnhub_api_key:
    raise ValueError("FINNHUB_API_KEY environment variable is required")

finnhub_client = finnhub.Client(api_key=finnhub_api_key)

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
index_cache = {}
news_highlighted_cache = {}


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
    try:
        if not raw_item or not isinstance(raw_item, dict):
            return None

        content = raw_item.get("content")
        if not content or not isinstance(content, dict):
            return None

        provider = content.get("provider") or {}
        urls = content.get("clickThroughUrl") or {}
        thumbnail = content.get("thumbnail") or {}
        finance_obj = content.get("finance") or {}
        finance = finance_obj.get("premiumFinance", {}) if isinstance(finance_obj, dict) else {}
        metadata = content.get("metadata") or {}

        thumbnail_urls = {}
        if isinstance(thumbnail, dict) and thumbnail.get("resolutions"):
            for res in thumbnail["resolutions"]:
                if isinstance(res, dict):
                    tag = res.get("tag", "")
                    thumbnail_urls[tag] = res.get("url")

        return {
            "id": content.get("id"),
            "title": content.get("title"),
            "summary": content.get("summary"),
            "datePublished": content.get("pubDate"),
            "provider": {
                "name": provider.get("displayName") if isinstance(provider, dict) else None,
                "url": provider.get("url") if isinstance(provider, dict) else None,
            },
            "articleUrl": urls.get("url") if isinstance(urls, dict) and urls else None,
            "thumbnail": thumbnail.get("originalUrl") if isinstance(thumbnail, dict) else None,
            "thumbnails": thumbnail_urls,
            "isPremium": finance.get("isPremiumNews", False) if isinstance(finance, dict) else False,
            "isEditorsPick": metadata.get("editorsPick", False) if isinstance(metadata, dict) else False,
        }
    except Exception:
        return None


def _extract_finnhub_news(raw_item: dict) -> dict:
    """Extract and normalize a news item from Finnhub API"""
    try:
        if not raw_item or not isinstance(raw_item, dict):
            return None

        timestamp = raw_item.get("datetime")
        date_published = None
        if timestamp:
            try:
                date_published = datetime.fromtimestamp(timestamp).isoformat() + "Z"
            except (ValueError, OSError, TypeError):
                date_published = None

        return {
            "id": raw_item.get("id"),
            "title": raw_item.get("headline"),
            "summary": raw_item.get("summary"),
            "datePublished": date_published,
            "provider": {
                "name": raw_item.get("source"),
                "url": raw_item.get("url"),
            },
            "articleUrl": raw_item.get("url"),
            "thumbnail": raw_item.get("image"),
            "thumbnails": {
                "original": raw_item.get("image"),
            },
            "isPremium": False,
            "isEditorsPick": False,
        }
    except Exception:
        return None


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

        news = [_extract_news_item(item) for item in raw_news if item]
        news = [item for item in news if item]

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


@app.get("/news/highlighted")
def api_news_highlighted(count: int = 10, min_id: int = 0):
    """
    Get highlighted/market news using Finnhub API with min_id pagination

    Parameters:
    - count: Number of news items to fetch (default: 10, max: 50)
    - min_id: Minimum news ID for pagination (default: 0, fetches latest)
      Use the last item's ID from previous request to fetch older news

    Returns: {"news": [...], "count": 10, "source": "finnhub", "next_min_id": ID}
    """
    if count > 50:
        count = 50
    if count < 1:
        count = 10
    if min_id < 0:
        min_id = 0

    cache_key = f"news_highlighted_{count}_{min_id}"

    if cache_key in news_highlighted_cache and is_cache_valid(cache_key, ttl_seconds=1800):
        cached_response = news_highlighted_cache[cache_key].copy()
        cached_response["cached"] = True
        return cached_response

    try:
        news_list = []
        last_item_id = 0

        raw_news = finnhub_client.general_news('general', min_id=min_id)
        if raw_news:
            for item in raw_news:
                if isinstance(item, dict):
                    extracted = _extract_finnhub_news(item)
                    if extracted:
                        news_list.append(extracted)
                    if "id" in item:
                        last_item_id = item.get("id", 0)

        paginated_news = news_list[:count]

        if not paginated_news:
            response = {
                "news": [],
                "count": 0,
                "source": "finnhub",
                "message": "No highlighted news available",
                "timestamp": datetime.now().isoformat(),
                "cached": False,
            }
            news_highlighted_cache[cache_key] = response
            cache_timestamps[cache_key] = datetime.now()
            return response

        next_min_id = last_item_id if len(news_list) >= count else 0

        response = {
            "news": paginated_news,
            "count": len(paginated_news),
            "next_min_id": next_min_id,
            "has_next": len(news_list) >= count,
            "source": "finnhub",
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        news_highlighted_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
        }


def _get_index_info(symbol: str) -> dict:
    """Get metadata for known indices"""
    indices = {
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
    return indices.get(symbol, {"name": "Unknown Index", "country": "N/A", "currency": "N/A"})


@app.get("/index/{symbol}/history")
def api_index_history(symbol: str, period: str = "1d", interval: str = "1m", limit: int = None):
    """
    Get historical price data for market indices

    Parameters:
    - symbol: Index ticker (e.g., ^JKSE for Indonesia, ^GSPC for S&P 500)
    - period: Time period - 1d, 2d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max (default: 1d)
    - interval: Data interval - 1d, 1wk, 1mo, 1h, 15m, 5m, 1m (default: 1m)
      Note: Intraday intervals (1h, 15m, 5m, 1m) require period >= 2d. Some indices like ^JKSE don't support intraday with period=1d.
    - limit: Optional cap on number of returned records (latest N)

    Returns: {"index": {...}, "data": [...], "count": X, "period": "..."}
    """
    cache_key = f"index_{symbol}_{period}_{interval}_{limit}"

    if cache_key in index_cache and is_cache_valid(cache_key, ttl_seconds=3600):
        cached_response = index_cache[cache_key].copy()
        cached_response["cached"] = True
        return cached_response

    try:
        if not symbol:
            return {"error": "symbol is required", "status": "failed"}

        supported_indices = ["^JKSE", "^GSPC", "^DJI", "^IXIC", "^N225", "^HSI", "^BVSP", "^FTSE", "^FCHI", "^GDAXI"]
        if symbol.upper() not in supported_indices:
            return {
                "error": f"Unsupported index: {symbol}",
                "status": "failed",
                "supported": supported_indices
            }

        hist = yf.download(symbol, period=period, interval=interval, progress=False)

        if hist.empty and interval in ["1m", "5m", "15m", "1h"] and period == "1d":
            return {
                "error": f"{symbol} does not support {interval} interval with period=1d",
                "status": "failed",
                "suggestion": f"Try: /index/{symbol}/history?period=2d&interval={interval} (minimum period for intraday is 2d)",
                "timestamp": datetime.now().isoformat(),
            }

        if hist.empty:
            return {
                "error": f"No data available for {symbol}",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
            }

        if isinstance(hist, pd.DataFrame) and not hist.empty:
            df = hist.reset_index()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if limit is not None and isinstance(limit, int) and limit > 0:
                df = df.tail(limit)

            history_json = df.to_json(orient="records", date_format="iso")
            data = json.loads(history_json)
        else:
            data = []

        index_info = _get_index_info(symbol)

        response = {
            "index": {
                "symbol": symbol,
                "name": index_info.get("name"),
                "country": index_info.get("country"),
                "currency": index_info.get("currency"),
            },
            "period": period,
            "interval": interval,
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        index_cache[cache_key] = response
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

