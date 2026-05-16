import json
from datetime import datetime

import pandas as pd
import yfinance as yf
from fastapi import APIRouter
from yfinance import EquityQuery

from core.cache import (
    gainers_cache, losers_cache, top_values_cache, top_volumes_cache,
    history_cache, news_cache, stock_detail_cache,
    keystats_cache, analysis_cache, financials_cache, profile_cache,
    cache_timestamps, is_cache_valid,
)
from core.news_utils import extract_news_item
from core.utils import serialize_value, serialize_dataframe, serialize_series_to_records, serialize_df_to_records

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
        actual_period = period

        if (hist is None or (isinstance(hist, pd.DataFrame) and hist.empty)) and period == "1d":
            for fallback_period in ["2d", "3d", "5d", "7d", "10d", "14d"]:
                hist = t.history(period=fallback_period, interval=interval)
                if hist is not None and isinstance(hist, pd.DataFrame) and not hist.empty:
                    break

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

            if previous_close and history and period == "1d":
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
            "period": actual_period,
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


@router.get("/{ticker}/keystats")
def api_stock_keystats(ticker: str):
    cache_key = f"keystats_{ticker}"
    if cache_key in keystats_cache and is_cache_valid(cache_key, ttl_seconds=900):
        cached = keystats_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        dividend_history = []
        try:
            dividend_history = serialize_series_to_records(t.dividends)
        except Exception:
            pass

        def _ts_to_iso(val):
            if val is None:
                return None
            try:
                from datetime import datetime, timezone
                return datetime.fromtimestamp(val, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                return None

        response = {
            "ticker": ticker,
            "valuation": {
                "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previousClose": info.get("previousClose"),
                "open": info.get("open"),
                "dayLow": info.get("dayLow"),
                "dayHigh": info.get("dayHigh"),
                "regularMarketChange": info.get("regularMarketChange"),
                "regularMarketChangePercent": info.get("regularMarketChangePercent"),
                "marketCap": info.get("marketCap"),
                "enterpriseValue": info.get("enterpriseValue"),
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "pegRatio": info.get("trailingPegRatio"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "enterpriseToRevenue": info.get("enterpriseToRevenue"),
                "enterpriseToEbitda": info.get("enterpriseToEbitda"),
                "beta": info.get("beta"),
                "volume": info.get("regularMarketVolume"),
                "averageVolume": info.get("averageVolume"),
                "averageVolume10days": info.get("averageVolume10days"),
                "shortRatio": info.get("shortRatio"),
                "shortPercentOfFloat": info.get("shortPercentOfFloat"),
            },
            "per_share": {
                "trailingEps": info.get("trailingEps") or info.get("epsTrailingTwelveMonths"),
                "forwardEps": info.get("forwardEps"),
                "bookValue": info.get("bookValue"),
                "revenuePerShare": info.get("revenuePerShare"),
                "totalCashPerShare": info.get("totalCashPerShare"),
            },
            "financial_summary": {
                "totalRevenue": info.get("totalRevenue"),
                "revenueGrowth": info.get("revenueGrowth"),
                "grossProfits": info.get("grossProfits"),
                "grossMargins": info.get("grossMargins"),
                "ebitda": info.get("ebitda"),
                "ebitdaMargins": info.get("ebitdaMargins"),
                "operatingMargins": info.get("operatingMargins"),
                "profitMargins": info.get("profitMargins"),
                "netIncomeToCommon": info.get("netIncomeToCommon"),
                "totalCash": info.get("totalCash"),
                "totalDebt": info.get("totalDebt"),
                "debtToEquity": info.get("debtToEquity"),
                "currentRatio": info.get("currentRatio"),
                "quickRatio": info.get("quickRatio"),
                "operatingCashflow": info.get("operatingCashflow"),
                "freeCashflow": info.get("freeCashflow"),
                "returnOnAssets": info.get("returnOnAssets"),
                "returnOnEquity": info.get("returnOnEquity"),
                "earningsGrowth": info.get("earningsGrowth"),
                "earningsQuarterlyGrowth": info.get("earningsQuarterlyGrowth"),
            },
            "dividend": {
                "dividendRate": info.get("dividendRate"),
                "dividendYield": info.get("dividendYield"),
                "trailingAnnualDividendRate": info.get("trailingAnnualDividendRate"),
                "trailingAnnualDividendYield": info.get("trailingAnnualDividendYield"),
                "fiveYearAvgDividendYield": info.get("fiveYearAvgDividendYield"),
                "payoutRatio": info.get("payoutRatio"),
                "exDividendDate": _ts_to_iso(info.get("exDividendDate")),
                "lastDividendValue": info.get("lastDividendValue"),
                "lastDividendDate": _ts_to_iso(info.get("lastDividendDate")),
                "history": dividend_history,
            },
            "price_performance": {
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "allTimeHigh": info.get("allTimeHigh"),
                "allTimeLow": info.get("allTimeLow"),
                "fiftyDayAverage": info.get("fiftyDayAverage"),
                "twoHundredDayAverage": info.get("twoHundredDayAverage"),
                "fiftyTwoWeekChange": info.get("52WeekChange"),
                "fiftyTwoWeekChangePercent": info.get("fiftyTwoWeekChangePercent"),
                "SandP52WeekChange": info.get("SandP52WeekChange"),
                "ytdReturn": info.get("ytdReturn"),
            },
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }
        keystats_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}/analysis")
def api_stock_analysis(ticker: str):
    cache_key = f"analysis_{ticker}"
    if cache_key in analysis_cache and is_cache_valid(cache_key, ttl_seconds=86400):
        cached = analysis_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        def _safe_records(fn, index_key="period"):
            try:
                return serialize_df_to_records(fn(), index_key=index_key) or None
            except Exception:
                return None

        def _safe_recommendations():
            try:
                df = t.recommendations
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    return None
                records = [
                    {str(col): serialize_value(row[col]) for col in df.columns}
                    for _, row in df.iterrows()
                ]
                return records or None
            except Exception:
                return None

        response = {
            "ticker": ticker,
            "recommendation": {
                "key": info.get("recommendationKey"),
                "mean": info.get("recommendationMean"),
                "numberOfAnalysts": info.get("numberOfAnalystOpinions"),
            },
            "price_targets": {
                "current": info.get("currentPrice") or info.get("regularMarketPrice"),
                "low": info.get("targetLowPrice"),
                "high": info.get("targetHighPrice"),
                "mean": info.get("targetMeanPrice"),
                "median": info.get("targetMedianPrice"),
            },
            "recommendations_trend": _safe_recommendations(),
            "earnings_estimate": _safe_records(lambda: t.earnings_estimate),
            "revenue_estimate": _safe_records(lambda: t.revenue_estimate),
            "earnings_history": _safe_records(lambda: t.earnings_history, index_key="date"),
            "eps_trend": _safe_records(lambda: t.eps_trend),
            "eps_revisions": _safe_records(lambda: t.eps_revisions),
            "growth_estimates": _safe_records(lambda: t.growth_estimates),
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }
        analysis_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}/financials")
def api_stock_financials_detail(ticker: str):
    cache_key = f"financials_{ticker}"
    if cache_key in financials_cache and is_cache_valid(cache_key, ttl_seconds=86400):
        cached = financials_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        t = yf.Ticker(ticker)

        def _safe_df(fn):
            try:
                return serialize_dataframe(fn())
            except Exception:
                return None

        response = {
            "ticker": ticker,
            "income_statement": {
                "annual": _safe_df(lambda: t.income_stmt),
                "quarterly": _safe_df(lambda: t.quarterly_income_stmt),
            },
            "balance_sheet": {
                "annual": _safe_df(lambda: t.balance_sheet),
                "quarterly": _safe_df(lambda: t.quarterly_balance_sheet),
            },
            "cash_flow": {
                "annual": _safe_df(lambda: t.cashflow),
                "quarterly": _safe_df(lambda: t.quarterly_cashflow),
            },
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }
        financials_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}/profile")
def api_stock_profile(ticker: str):
    cache_key = f"profile_{ticker}"
    if cache_key in profile_cache and is_cache_valid(cache_key, ttl_seconds=86400):
        cached = profile_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        officers = info.get("companyOfficers", [])
        if isinstance(officers, list):
            officers = [serialize_value(o) for o in officers]
        else:
            officers = []

        response = {
            "ticker": ticker,
            "company": {
                "name": info.get("longName") or info.get("shortName"),
                "shortName": info.get("shortName"),
                "symbol": info.get("symbol"),
                "exchange": info.get("fullExchangeName"),
                "exchangeCode": info.get("exchange"),
                "market": info.get("market"),
                "currency": info.get("currency"),
                "financialCurrency": info.get("financialCurrency"),
                "quoteType": info.get("quoteType"),
                "ipoDate": info.get("ipoExpectedDate"),
                "firstTradeDateMilliseconds": info.get("firstTradeDateMilliseconds"),
                "fullTimeEmployees": info.get("fullTimeEmployees"),
                "irWebsite": info.get("irWebsite"),
            },
            "address": {
                "address1": info.get("address1"),
                "address2": info.get("address2"),
                "city": info.get("city"),
                "state": info.get("state"),
                "zip": info.get("zip"),
                "country": info.get("country"),
                "phone": info.get("phone"),
                "fax": info.get("fax"),
                "website": info.get("website"),
            },
            "overview": {
                "sector": info.get("sector"),
                "sectorKey": info.get("sectorKey"),
                "sectorDisp": info.get("sectorDisp"),
                "industry": info.get("industry"),
                "industryKey": info.get("industryKey"),
                "industryDisp": info.get("industryDisp"),
                "description": info.get("longBusinessSummary"),
            },
            "ownership": {
                "heldPercentInsiders": info.get("heldPercentInsiders"),
                "heldPercentInstitutions": info.get("heldPercentInstitutions"),
                "sharesOutstanding": info.get("sharesOutstanding"),
                "floatShares": info.get("floatShares"),
                "impliedSharesOutstanding": info.get("impliedSharesOutstanding"),
            },
            "governance": {
                "auditRisk": info.get("auditRisk"),
                "boardRisk": info.get("boardRisk"),
                "compensationRisk": info.get("compensationRisk"),
                "shareHolderRightsRisk": info.get("shareHolderRightsRisk"),
                "overallRisk": info.get("overallRisk"),
            },
            "officers": officers,
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }
        profile_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}


@router.get("/{ticker}")
def api_stock_detail(ticker: str):
    cache_key = f"stock_detail_{ticker}"
    if cache_key in stock_detail_cache and is_cache_valid(cache_key):
        cached = stock_detail_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        if not ticker:
            return {"error": "ticker is required", "status": "failed"}

        try:
            raw_info = yf.Ticker(ticker).info or {}
        except Exception:
            raw_info = {}

        serialized_raw = {k: serialize_value(v) for k, v in raw_info.items()} if isinstance(raw_info, dict) else {}

        response = {
            "ticker": ticker,
            "raw_info": serialized_raw,
            "cached": False,
            "timestamp": datetime.now().isoformat(),
        }
        stock_detail_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}

