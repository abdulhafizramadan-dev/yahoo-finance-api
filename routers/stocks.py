import json
from datetime import datetime

import pandas as pd
import yfinance as yf
from fastapi import APIRouter
from yfinance import EquityQuery

from core.cache import (
    gainers_cache, losers_cache, top_values_cache, top_volumes_cache,
    history_cache, news_cache, cache_timestamps, is_cache_valid,
)
from core.news_utils import extract_news_item
from core.utils import serialize_value

router = APIRouter(prefix="/stocks", tags=["stocks"])


def _build_stock(q: dict) -> dict:
    return {
        "ticker": q.get("symbol", "N/A"),
        "name": q.get("shortName", "N/A"),
        "price": q.get("regularMarketPrice", 0),
        "change_value": round(q.get("regularMarketChange", 0), 2),
        "change_percent": round(q.get("regularMarketChangePercent", 0), 2),
        "volume": q.get("regularMarketVolume", 0),
        "market_cap": q.get("marketCap", 0),
    }


@router.get("/gainers")
def api_gainers(limit: int = 10, region: str = "id"):
    cache_key = f"gainers_{region}_{limit}"
    if cache_key in gainers_cache and is_cache_valid(cache_key):
        cached = gainers_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('gt', ['percentchange', 0]),
        ])
        result = yf.screen(query, sortField='percentchange', sortAsc=False, size=limit)
        quotes = result.get('quotes', [])

        response = {
            "stocks": [_build_stock(q) for q in quotes],
            "count": len(quotes),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        gainers_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/losers")
def api_losers(limit: int = 10, region: str = "id"):
    cache_key = f"losers_{region}_{limit}"
    if cache_key in losers_cache and is_cache_valid(cache_key):
        cached = losers_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('lt', ['percentchange', 0]),
        ])
        result = yf.screen(query, sortField='percentchange', sortAsc=True, size=limit)
        quotes = result.get('quotes', [])

        response = {
            "stocks": [_build_stock(q) for q in quotes],
            "count": len(quotes),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        losers_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/top-values")
def api_top_values(limit: int = 10, region: str = "id"):
    cache_key = f"top_values_{region}_{limit}"
    if cache_key in top_values_cache and is_cache_valid(cache_key):
        cached = top_values_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('gt', ['dayvolume', 0]),
        ])
        result = yf.screen(query, sortField='dayvolume', sortAsc=False, size=200)
        quotes = result.get('quotes', [])

        stocks = []
        for q in quotes:
            price = q.get("regularMarketPrice") or 0
            volume = q.get("regularMarketVolume") or 0
            transaction_value = price * volume
            stock = _build_stock(q)
            stock["transaction_value"] = round(transaction_value, 2)
            stocks.append(stock)

        stocks.sort(key=lambda x: x["transaction_value"], reverse=True)
        stocks = stocks[:limit]

        response = {
            "stocks": stocks,
            "count": len(stocks),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        top_values_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/top-volumes")
def api_top_volumes(limit: int = 10, region: str = "id"):
    cache_key = f"top_volumes_{region}_{limit}"
    if cache_key in top_volumes_cache and is_cache_valid(cache_key):
        cached = top_volumes_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if limit > 50:
            limit = 50

        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('gt', ['dayvolume', 0]),
        ])
        result = yf.screen(query, sortField='dayvolume', sortAsc=False, size=limit)
        quotes = result.get('quotes', [])

        response = {
            "stocks": [_build_stock(q) for q in quotes],
            "count": len(quotes),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        top_volumes_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}/history")
def api_stock_history(ticker: str, period: str = "1mo", interval: str = "1d", limit: int = None):
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

        previous_close = None
        try:
            previous_close = t.fast_info.get("previousClose") or t.fast_info.get("regular_market_previous_close")
        except Exception:
            pass

        if isinstance(hist, pd.DataFrame) and not hist.empty:
            df = hist.reset_index()
            if limit is not None and isinstance(limit, int) and limit > 0:
                df = df.tail(limit)
            history = json.loads(df.to_json(orient="records", date_format="iso"))

            if previous_close and history:
                date_key = "Datetime" if "Datetime" in history[0] else "Date"
                first_ts = pd.Timestamp(history[0][date_key])
                prev_ts = (first_ts - pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
                synthetic = {
                    date_key: prev_ts,
                    "Open": previous_close,
                    "High": previous_close,
                    "Low": previous_close,
                    "Close": previous_close,
                    "Volume": 0,
                }
                history = [synthetic] + history

            count = len(history)
        else:
            history, count = [], 0

        response = {
            "ticker": ticker,
            "previous_close": previous_close,
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


@router.get("/{ticker}/news")
def api_stock_news(ticker: str, count: int = 10, tab: str = "all"):
    cache_key = f"news_{ticker}_{count}_{tab}"
    if cache_key in news_cache and is_cache_valid(cache_key, ttl_seconds=1800):
        cached = news_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if count > 50:
            count = 50
        if tab not in ["news", "all", "press releases"]:
            tab = "news"

        raw_news = yf.Ticker(ticker).get_news(count=count, tab=tab)

        if not raw_news:
            response = {
                "news": [], "count": 0, "ticker": ticker, "newsType": tab,
                "message": "No news available for this ticker",
                "timestamp": datetime.now().isoformat(), "cached": False,
            }
            news_cache[cache_key] = response
            cache_timestamps[cache_key] = datetime.now()
            return response

        news = [item for item in (extract_news_item(i) for i in raw_news if i) if item]

        response = {
            "news": news, "count": len(news), "ticker": ticker, "newsType": tab,
            "timestamp": datetime.now().isoformat(), "cached": False,
        }
        news_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "ticker": ticker, "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}")
def api_stock_detail(ticker: str):
    try:
        if not ticker:
            return {"error": "ticker is required", "status": "failed"}

        try:
            raw_info = yf.Ticker(ticker).info or {}
        except Exception:
            raw_info = {}

        serialized_raw = {k: serialize_value(v) for k, v in raw_info.items()} if isinstance(raw_info, dict) else {}

        return {"ticker": ticker, "raw_info": serialized_raw, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}

