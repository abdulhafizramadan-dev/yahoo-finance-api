import json
from datetime import datetime

import pandas as pd
import yfinance as yf
from fastapi import APIRouter

from config import SUPPORTED_INDICES, INDEX_INFO_MAP
from core.cache import index_cache, cache_timestamps, is_cache_valid

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/{symbol}/history")
def api_index_history(symbol: str, period: str = "1d", interval: str = "1m", limit: int = None):
    cache_key = f"index_{symbol}_{period}_{interval}_{limit}"
    if cache_key in index_cache and is_cache_valid(cache_key, ttl_seconds=3600):
        cached = index_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if not symbol:
            return {"error": "symbol is required", "status": "failed"}

        if symbol.upper() not in SUPPORTED_INDICES:
            return {
                "error": f"Unsupported index: {symbol}",
                "status": "failed",
                "supported": SUPPORTED_INDICES,
            }

        hist = yf.download(symbol, period=period, interval=interval, progress=False)

        if hist.empty and period == "1d":
            hist = yf.download(symbol, period="2d", interval=interval, progress=False)

        if hist.empty and interval in ["1m", "5m", "15m", "1h"]:
            return {
                "error": f"{symbol} does not support {interval} interval with period=1d or 2d",
                "status": "failed",
                "suggestion": f"Try: /index/{symbol}/history?period=5d&interval={interval}",
                "timestamp": datetime.now().isoformat(),
            }

        if hist.empty:
            return {"error": f"No data available for {symbol}", "status": "failed", "timestamp": datetime.now().isoformat()}

        previous_close = None
        try:
            previous_close = yf.Ticker(symbol).fast_info.get("previousClose") or yf.Ticker(symbol).fast_info.get("regular_market_previous_close")
        except Exception:
            pass

        df = hist.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if limit is not None and isinstance(limit, int) and limit > 0:
            df = df.tail(limit)

        data = json.loads(df.to_json(orient="records", date_format="iso"))

        if previous_close and data:
            date_key = "Datetime" if "Datetime" in data[0] else "Date"
            first_ts = pd.Timestamp(data[0][date_key])
            prev_ts = (first_ts - pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            synthetic = {
                date_key: prev_ts,
                "Open": previous_close,
                "High": previous_close,
                "Low": previous_close,
                "Close": previous_close,
                "Volume": 0,
            }
            data = [synthetic] + data
        index_info = INDEX_INFO_MAP.get(symbol, {"name": "Unknown Index", "country": "N/A", "currency": "N/A"})

        response = {
            "index": {
                "symbol": symbol,
                "name": index_info.get("name"),
                "country": index_info.get("country"),
                "currency": index_info.get("currency"),
            },
            "previous_close": previous_close,
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
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}

