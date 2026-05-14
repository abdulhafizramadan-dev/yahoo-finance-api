from datetime import datetime

import yfinance as yf
from fastapi import APIRouter
from yfinance import EquityQuery

from config import YAHOO_SECTORS, SECTOR_KEY_MAP
from core.cache import sectors_cache, cache_timestamps, is_cache_valid

router = APIRouter(prefix="/sectors", tags=["sectors"])


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


@router.get("/summary")
def api_sectors_summary(region: str = "id"):
    cache_key = f"sectors_{region}"
    if cache_key in sectors_cache and is_cache_valid(cache_key, ttl_seconds=300):
        cached = sectors_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        sectors_result = []

        for sector in YAHOO_SECTORS:
            try:
                query = EquityQuery('and', [
                    EquityQuery('eq', ['region', region]),
                    EquityQuery('eq', ['sector', sector["name"]]),
                ])
                result = yf.screen(query, sortField='percentchange', sortAsc=False, size=250)
                quotes = result.get('quotes', []) if result else []

                changes = [
                    q.get('regularMarketChangePercent')
                    for q in quotes
                    if q.get('regularMarketChangePercent') is not None
                ]
                if not changes:
                    continue

                avg_change = round(sum(changes) / len(changes), 2)
                direction = "up" if avg_change > 0 else ("down" if avg_change < 0 else "flat")

                sectors_result.append({
                    "name": sector["name"],
                    "key": sector["key"],
                    "displayName": sector["displayName"],
                    "change_percent": avg_change,
                    "stock_count": len(changes),
                    "direction": direction,
                })
            except Exception:
                continue

        sectors_result.sort(key=lambda x: x["change_percent"], reverse=True)

        response = {
            "sectors": sectors_result,
            "count": len(sectors_result),
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        sectors_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "region": region, "timestamp": datetime.now().isoformat()}


@router.get("/{sector_key}/stocks")
def api_sector_stocks(sector_key: str, region: str = "id"):
    sector = SECTOR_KEY_MAP.get(sector_key)
    if not sector:
        return {
            "error": f"Unknown sector key: '{sector_key}'",
            "status": "failed",
            "supported_keys": list(SECTOR_KEY_MAP.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    cache_key = f"sector_stocks_{sector_key}_{region}"
    if cache_key in sectors_cache and is_cache_valid(cache_key, ttl_seconds=300):
        cached = sectors_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        query = EquityQuery('and', [
            EquityQuery('eq', ['region', region]),
            EquityQuery('eq', ['sector', sector["name"]]),
        ])
        result = yf.screen(query, sortField='percentchange', sortAsc=False, size=250)
        quotes = result.get('quotes', []) if result else []

        response = {
            "stocks": [_build_stock(q) for q in quotes],
            "count": len(quotes),
            "sector": {
                "name": sector["name"],
                "key": sector["key"],
                "displayName": sector["displayName"],
            },
            "region": region,
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        sectors_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "sector_key": sector_key, "region": region, "timestamp": datetime.now().isoformat()}

