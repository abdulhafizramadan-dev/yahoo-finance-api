# Yahoo Finance API Specification
**v1.3** | Base URL: `http://localhost:8000` | Focus: Indonesia Stock Market (IDX)

---

## Endpoints

| Method | Path | Purpose | Cache |
|--------|------|---------|-------|
| GET | `/health` | API status | — |
| GET | `/stocks/gainers` | Top gaining stocks | 5 min |
| GET | `/stocks/losers` | Top losing stocks | 5 min |
| GET | `/stocks/{ticker}` | Full stock info (`raw_info`) | 5 min |
| GET | `/stocks/{ticker}/history` | OHLCV price history | 5 min |
| GET | `/stocks/{ticker}/news` | Stock-specific news | 30 min |
| GET | `/news/highlighted` | General market news (Finnhub) | 30 min |
| GET | `/index/{symbol}/history` | Market index OHLCV | 1 hour |
| GET | `/sectors/summary` | Sector % change today | 5 min |
| GET | `/sectors/{sector_key}/stocks` | Stocks within a sector | 5 min |

---

## Common Response Fields
All responses include `"cached": bool` and `"timestamp": ISO8601`.  
Errors always return `{"error": "...", "status": "failed", "timestamp": "..."}`.

---

## Stock Object (shared across gainers, losers, sector stocks)
```json
{
  "ticker": "BBCA.JK",
  "name": "PT Bank Central Asia Tbk",
  "price": 5850.0,
  "change_value": 150.0,
  "change_percent": 2.50,
  "volume": 303405400,
  "market_cap": 718825993535488
}
```

---

## 1. GET `/stocks/gainers` & `/stocks/losers`
**Params:** `limit` (int, 1–50, default 10) · `region` (str, default `"id"`)  
**Response:** `{ "stocks": [Stock], "count": int, "region": str }`

---

## 2. GET `/stocks/{ticker}`
**Response:** `{ "ticker": str, "raw_info": { ...full yfinance info dict... } }`  
Key fields in `raw_info`: `regularMarketPrice`, `regularMarketChange`, `regularMarketChangePercent`, `marketCap`, `sector`, `industry`, `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`, `trailingPE`, `dividendYield`.

---

## 3. GET `/stocks/{ticker}/history`
**Params:** `period` (default `1mo`) · `interval` (default `1d`) · `limit` (optional, latest N)  
**Response:** `{ "ticker", "history": [{ "Date", "Open", "High", "Low", "Close", "Volume" }], "count", "period", "interval" }`

---

## 4. GET `/stocks/{ticker}/news`
**Params:** `count` (1–50, default 10) · `tab` (`"all"` | `"news"` | `"press releases"`, default `"all"`)  
**Response:** `{ "news": [NewsItem], "count", "ticker", "newsType" }`

**NewsItem:**
```json
{
  "id": "abc123",
  "title": "...",
  "summary": "...",
  "datePublished": "2026-05-05T08:30:00Z",
  "provider": { "name": "Reuters", "url": "https://reuters.com" },
  "articleUrl": "https://...",
  "thumbnail": "https://...",
  "isPremium": false,
  "isEditorsPick": true
}
```

---

## 5. GET `/news/highlighted`
**Params:** `count` (1–50, default 10) · `min_id` (int, default 0 = latest)  
**Response:** `{ "news": [NewsItem], "count", "next_min_id": int, "has_next": bool, "source": "finnhub" }`  
**Pagination:** pass `min_id=next_min_id` from previous response to fetch older news.  
> ⚠️ `datePublished` is converted from Unix timestamp to ISO 8601.

---

## 6. GET `/index/{symbol}/history`
**Params:** `period` (default `1d`) · `interval` (default `1m`) · `limit` (optional)  
**Response:** `{ "index": { "symbol", "name", "country", "currency" }, "data": [{ "Datetime", "Open", "High", "Low", "Close", "Volume" }], "count", "period", "interval" }`

**Supported symbols:** `^JKSE` (Indonesia), `^GSPC`, `^DJI`, `^IXIC`, `^N225`, `^HSI`, `^BVSP`, `^FTSE`, `^FCHI`, `^GDAXI`

> ⚠️ Intraday intervals (`1m`, `5m`, `15m`, `1h`) require `period >= 2d` for `^JKSE`.

---

## 7. GET `/sectors/summary`
**Params:** `region` (default `"id"`)  
**Response:** `{ "sectors": [SectorItem], "count", "region" }`  

**SectorItem:**
```json
{
  "name": "Financial Services",
  "key": "financial-services",
  "displayName": "FINANCIAL",
  "change_percent": -0.44,
  "stock_count": 100,
  "direction": "up" | "down" | "flat"
}
```

> ⚠️ First load is slow (~5–8s) — makes 11 upstream calls. Rely on cache after first hit.

---

## 8. GET `/sectors/{sector_key}/stocks`
**Params:** `region` (default `"id"`) · `limit` (1–100, default 50)  
**Response:** `{ "stocks": [Stock], "count", "sector": { "name", "key", "displayName" }, "region" }`  
**Invalid key error:** includes `"supported_keys": [...]`

**Supported sector keys:**

| Key | `displayName` |
|-----|--------------|
| `financial-services` | `FINANCIAL` |
| `energy` | `ENERGY` |
| `technology` | `TECHNOLOGY` |
| `basic-materials` | `MATERIAL` |
| `consumer-cyclical` | `CYCLICAL` |
| `consumer-defensive` | `NON-CYCLICAL` |
| `healthcare` | `HEALTH` |
| `industrials` | `INDUSTRIAL` |
| `real-estate` | `PROPERTY` |
| `utilities` | `UTILITY` |
| `communication-services` | `TELECOM` |

---

## Cache Keys Reference

| Endpoint | Key pattern |
|----------|-------------|
| Gainers/Losers | `gainers_{region}_{limit}` / `losers_{region}_{limit}` |
| Stock History | `history_{ticker}_{period}_{interval}_{limit}` |
| Stock News | `news_{ticker}_{count}_{tab}` |
| Highlighted News | `news_highlighted_{count}_{min_id}` |
| Index History | `index_{symbol}_{period}_{interval}_{limit}` |
| Sectors Summary | `sectors_{region}` |
| Sector Stocks | `sector_stocks_{sector_key}_{region}_{limit}` |

---

*Last Updated: May 11, 2026*
