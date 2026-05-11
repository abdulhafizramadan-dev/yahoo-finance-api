# Yahoo Finance API Specification
## StockBit Mini App - API Contract

**Version:** 1.3  
**Date:** May 11, 2026  
**Base URL:** `http://localhost:8000` (Development) | `https://your-api.onrender.com` (Production)  
**Focus:** Indonesia Stock Market (IDX)

---

## Quick Reference

| Endpoint | Method | Purpose | Server Cache |
|----------|--------|---------|-----------|
| `/health` | GET | Health check | None |
| `/stocks/gainers` | GET | Top gaining stocks | 5 min |
| `/stocks/losers` | GET | Top losing stocks | 5 min |
| `/stocks/{ticker}` | GET | Stock details | 5 min |
| `/stocks/{ticker}/history` | GET | Price history (OHLCV) | 5 min |
| `/stocks/{ticker}/news` | GET | Stock news feed | 30 min |
| `/news/highlighted` | GET | Market/highlighted news | 30 min |
| `/index/{symbol}/history` | GET | Market index data | 1 hour |
| `/sectors/summary` | GET | Sector performance summary | 5 min |
| `/sectors/{sector_key}/stocks` | GET | Stocks list by sector | 5 min |

---

## Common Response Format

### Success Response
```json
{
  "data": {...},
  "count": 10,
  "timestamp": "2026-05-06T10:30:00.123456",
  "cached": false
}
```

### Error Response
```json
{
  "error": "Error description",
  "status": "failed",
  "timestamp": "2026-05-06T10:30:00.123456"
}
```

---

## 1. Health Check

**Purpose:** Check if API is running

**Endpoint:** `GET /health`

**Parameters:** None

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-05-06T10:30:00.123456",
  "service": "Yahoo Finance API",
  "version": "0.1.0"
}
```

**Usage:**
- Call on app launch to verify API availability
- Use for monitoring/alerting
- No caching needed

---

## 2. Top Gainers

**Purpose:** Get stocks with highest positive price change

**Endpoint:** `GET /stocks/gainers`

**Parameters:**

| Name | Type | Default | Required | Constraints | Description |
|------|------|---------|----------|-------------|-------------|
| `limit` | int | 10 | No | 1-50 | Number of stocks to return |
| `region` | string | "id" | No | 2-char code | Market region (Indonesia) |

**Example Request:**
```bash
GET /stocks/gainers?limit=10&region=id
```

**Response:**
```json
{
  "stocks": [
    {
      "ticker": "BBCA.JK",
      "name": "PT Bank Central Asia Tbk",
      "price": 5850.0,
      "change_value": 150.0,
      "change_percent": 2.50,
      "volume": 303405400,
      "market_cap": 718825993535488
    },
    {
      "ticker": "ASII.JK",
      "name": "PT Astra International Tbk",
      "price": 5475.0,
      "change_value": 99.38,
      "change_percent": 1.85,
      "volume": 45236800,
      "market_cap": 168234567890123
    }
  ],
  "count": 10,
  "region": "id",
  "timestamp": "2026-05-11T10:30:00.123456",
  "cached": false
}
```

**Stock Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock symbol (e.g., "BBCA.JK") |
| `name` | string | Company short name |
| `price` | float | Current market price |
| `change_value` | float | Absolute price change today (e.g., +150.0 IDR) |
| `change_percent` | float | Percentage price change today (e.g., +2.50%) |
| `volume` | int | Today's trading volume |
| `market_cap` | int | Market capitalization |

**Error Scenarios:**
- Invalid region → Returns empty list
- Limit > 50 → Automatically capped at 50

**Notes:**
- Server caches response for 5 minutes
- Data refreshed on every uncached request
- Pull-to-refresh recommended for client

---

## 3. Top Losers

**Purpose:** Get stocks with highest negative price change

**Endpoint:** `GET /stocks/losers`

**Parameters:**

| Name | Type | Default | Required | Constraints | Description |
|------|------|---------|----------|-------------|-------------|
| `limit` | int | 10 | No | 1-50 | Number of stocks to return |
| `region` | string | "id" | No | 2-char code | Market region (Indonesia) |

**Example Request:**
```bash
GET /stocks/losers?limit=10&region=id
```

**Response:** (Same structure as Gainers)
```json
{
  "stocks": [
    {
      "ticker": "ADHI.JK",
      "name": "PT Adhi Karya Tbk",
      "price": 245.0,
      "change_value": -7.97,
      "change_percent": -3.15,
      "volume": 12345678,
      "market_cap": 5678901234567
    }
  ],
  "count": 10,
  "region": "id",
  "timestamp": "2026-05-11T10:30:00.123456",
  "cached": false
}
```

**Usage Tips:**
- Combine with Gainers for "Biggest Movers" view
- Sort by absolute value of change_percent
- Use red color for negative values
- Display with down arrow (▼)

---

## 4. Stock Details

**Purpose:** Get comprehensive stock information

**Endpoint:** `GET /stocks/{ticker}`

**Path Parameters:**

| Name | Type | Required | Example | Description |
|------|------|----------|---------|-------------|
| `ticker` | string | Yes | "BBCA.JK" | Stock ticker symbol |

**Query Parameters:**

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `period` | string | "1mo" | No | Not used (legacy) |
| `interval` | string | "1d" | No | Not used (legacy) |

**Example Request:**
```bash
GET /stocks/BBCA.JK
```

**Response:**
```json
{
  "ticker": "BBCA.JK",
  "raw_info": {
    "symbol": "BBCA.JK",
    "shortName": "PT Bank Central Asia Tbk",
    "longName": "PT Bank Central Asia Tbk.",
    "currency": "IDR",
    "regularMarketPrice": 5850.0,
    "regularMarketPreviousClose": 5700.0,
    "regularMarketChange": 150.0,
    "regularMarketChangePercent": 2.63,
    "regularMarketVolume": 303405400,
    "averageVolume": 250000000,
    "marketCap": 718825993535488,
    "fiftyTwoWeekHigh": 9800.0,
    "fiftyTwoWeekLow": 5800.0,
    "fiftyDayAverage": 7200.0,
    "twoHundredDayAverage": 7500.0,
    "trailingPE": 15.3,
    "forwardPE": 14.8,
    "dividendRate": 250.0,
    "dividendYield": 0.0427,
    "beta": 1.05,
    "bookValue": 2850.0,
    "priceToBook": 2.05,
    "sector": "Financial Services",
    "industry": "Banks - Regional",
    "fullTimeEmployees": 25000
  },
  "timestamp": "2026-05-06T10:30:00.123456"
}
```

**Error Scenarios:**
```json
{
  "error": "ticker is required",
  "status": "failed"
}
```

**Important Fields:**
- `regularMarketPrice` - Current price (large, bold)
- `regularMarketChangePercent` - % change (green/red)
- `marketCap` - Market capitalization
- `fiftyTwoWeekHigh/Low` - 52-week range
- `trailingPE` - P/E ratio
- `dividendRate` - Dividend per share

---

## 5. Stock Price History

**Purpose:** Get OHLCV data for charting

**Endpoint:** `GET /stocks/{ticker}/history`

**Path Parameters:**

| Name | Type | Required | Example | Description |
|------|------|----------|---------|-------------|
| `ticker` | string | Yes | "BBCA.JK" | Stock ticker symbol |

**Query Parameters:**

| Name | Type | Default | Options | Description |
|------|------|---------|---------|-------------|
| `period` | string | "1mo" | 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max | Time period |
| `interval` | string | "1d" | 1m, 5m, 15m, 1h, 1d, 1wk, 1mo | Data interval |
| `limit` | int | null | Any positive int | Limit records (latest N) |

**Example Request:**
```bash
GET /stocks/BBCA.JK/history?period=1mo&interval=1d&limit=30
```

**Response:**
```json
{
  "ticker": "BBCA.JK",
  "history": [
    {
      "Date": "2026-04-01T00:00:00.000Z",
      "Open": 7100.0,
      "High": 7150.0,
      "Low": 7050.0,
      "Close": 7125.0,
      "Volume": 250000000,
      "Dividends": 0,
      "Stock Splits": 0
    },
    {
      "Date": "2026-04-02T00:00:00.000Z",
      "Open": 7125.0,
      "High": 7200.0,
      "Low": 7100.0,
      "Close": 7180.0,
      "Volume": 280000000,
      "Dividends": 0,
      "Stock Splits": 0
    }
  ],
  "count": 30,
  "period": "1mo",
  "interval": "1d",
  "cached": false,
  "timestamp": "2026-05-06T10:30:00.123456"
}
```

**Common Period/Interval Combinations:**
- 1D (intraday) - Use interval: 15m or 1h
- 1W - Use interval: 1h or 1d
- 1M - Use interval: 1d
- 6M - Use interval: 1d
- 1Y - Use interval: 1wk
- 5Y - Use interval: 1mo

---

## 6. Stock News Feed

**Purpose:** Get news articles for a specific stock

**Endpoint:** `GET /stocks/{ticker}/news`

**Path Parameters:**

| Name | Type | Required | Example | Description |
|------|------|----------|---------|-------------|
| `ticker` | string | Yes | "BBCA.JK" | Stock ticker symbol |

**Query Parameters:**

| Name | Type | Default | Options | Description |
|------|------|---------|---------|-------------|
| `count` | int | 10 | 1-50 | Number of news items |
| `tab` | string | "all" | "news", "all", "press releases" | News type filter |

**Example Request:**
```bash
GET /stocks/BBCA.JK/news?count=10&tab=all
```

**Response:**
```json
{
  "news": [
    {
      "id": "abc123",
      "title": "PT Bank Central Asia Reports Strong Q1 Earnings",
      "summary": "BCA reported net profit of Rp 10.2T for Q1 2026, up 12% YoY...",
      "datePublished": "2026-05-05T08:30:00Z",
      "provider": {
        "name": "Reuters",
        "url": "https://reuters.com"
      },
      "articleUrl": "https://finance.yahoo.com/news/bca-earnings-123456",
      "thumbnail": "https://s.yimg.com/uu/api/res/1.2/abc123",
      "thumbnails": {
        "original": "https://s.yimg.com/.../original.jpg",
        "resized_200": "https://s.yimg.com/.../200x200.jpg"
      },
      "isPremium": false,
      "isEditorsPick": true
    }
  ],
  "count": 10,
  "ticker": "BBCA.JK",
  "newsType": "all",
  "timestamp": "2026-05-06T10:30:00.123456",
  "cached": false
}
```

**Empty State Response:**
```json
{
  "news": [],
  "count": 0,
  "ticker": "UNKNOWN.JK",
  "newsType": "all",
  "message": "No news available for this ticker",
  "timestamp": "2026-05-06T10:30:00.123456",
  "cached": false
}
```

**Notes:**
- News items typically include thumbnails for display
- `isPremium` indicates paywall content
- `isEditorsPick` highlights important news
- Empty results return message field

---

## 7. Highlighted Market News

**Purpose:** Get general market/highlighted news using Finnhub API

**Endpoint:** `GET /news/highlighted`

**Query Parameters:**

| Name | Type | Default | Options | Description |
|------|------|---------|---------|-------------|
| `count` | int | 10 | 1-50 | Number of news items to fetch per request |
| `min_id` | int | 0 | Any positive int | News ID for pagination (default fetches latest) |

**Example Requests:**
```bash
# Get first page (latest 10)
GET /news/highlighted?count=10

# Get next page using min_id from previous response
GET /news/highlighted?count=10&min_id=1234567890
```

**Response (First Page):**
```json
{
  "news": [
    {
      "id": "xyz789",
      "title": "Federal Reserve Hints at Rate Cut",
      "summary": "Central bank signals potential monetary easing ahead...",
      "datePublished": "2026-05-09T15:30:00Z",
      "provider": {
        "name": "Reuters",
        "url": "https://reuters.com"
      },
      "articleUrl": "https://bloomberg.com/news/articles/fed-rate-cut",
      "thumbnail": "https://images.unsplash.com/photo-fed",
      "thumbnails": {
        "original": "https://images.unsplash.com/photo-fed"
      },
      "isPremium": false,
      "isEditorsPick": true
    },
    {
      "id": "xyz788",
      "title": "Tech Stock Rally Continues",
      "summary": "Major tech indices hit new record highs...",
      "datePublished": "2026-05-09T14:15:00Z",
      "provider": {
        "name": "Bloomberg",
        "url": "https://bloomberg.com"
      },
      "articleUrl": "https://bloomberg.com/news/articles/tech-rally",
      "thumbnail": "https://images.unsplash.com/photo-tech",
      "thumbnails": {
        "original": "https://images.unsplash.com/photo-tech"
      },
      "isPremium": false,
      "isEditorsPick": false
    }
  ],
  "count": 2,
  "next_min_id": 1234567890,
  "has_next": true,
  "source": "finnhub",
  "timestamp": "2026-05-09T16:00:00.123456",
  "cached": false
}
```

**Empty State Response:**
```json
{
  "news": [],
  "count": 0,
  "source": "finnhub",
  "message": "No highlighted news available",
  "timestamp": "2026-05-09T16:00:00.123456",
  "cached": false
}
```

**Pagination Pattern:**
1. First request: `GET /news/highlighted?count=10`
2. Response includes `next_min_id` (e.g., 1234567890) and `has_next: true`
3. Next request: `GET /news/highlighted?count=10&min_id=1234567890`
4. Continue until `has_next: false` indicates no more news

**Important Notes:**
- Server caches news for 30 minutes
- Uses Finnhub general news API for comprehensive market coverage
- `next_min_id` from response should be used as `min_id` in next request
- `has_next: false` indicates you've reached the end of available news
- Same news structure as stock-specific news feed
- Source is always "finnhub" for this endpoint

---

## 8. Market Index History

**Purpose:** Get market index data for charts (e.g., IHSG/^JKSE)

**Endpoint:** `GET /index/{symbol}/history`

**Path Parameters:**

| Name | Type | Required | Example | Description |
|------|------|----------|---------|-------------|
| `symbol` | string | Yes | "^JKSE" | Index symbol |

**Supported Indices:**

| Symbol | Name | Country |
|--------|------|---------|
| **^JKSE** | IDX Composite | Indonesia 🇮🇩 |
| ^GSPC | S&P 500 | USA |
| ^DJI | Dow Jones | USA |
| ^IXIC | NASDAQ | USA |
| ^N225 | Nikkei 225 | Japan |
| ^HSI | Hang Seng | Hong Kong |
| ^BVSP | Bovespa | Brazil |
| ^FTSE | FTSE 100 | UK |
| ^FCHI | CAC 40 | France |
| ^GDAXI | DAX | Germany |

**Query Parameters:**

| Name | Type | Default | Options | Description |
|------|------|---------|---------|-------------|
| `period` | string | "1d" | 1d, 2d, 5d, 1mo, 3mo, 6mo, 1y, max | Time period |
| `interval` | string | "1m" | 1m, 5m, 15m, 1h, 1d, 1wk, 1mo | Data interval |
| `limit` | int | null | Any positive int | Limit records (latest N) |

**Example Request:**
```bash
GET /index/^JKSE/history?period=1d&interval=15m&limit=50
```

**Response:**
```json
{
  "index": {
    "symbol": "^JKSE",
    "name": "IDX Composite",
    "country": "Indonesia",
    "currency": "IDR"
  },
  "period": "1d",
  "interval": "15m",
  "data": [
    {
      "Datetime": "2026-05-08T02:00:00.000Z",
      "Open": 7182.9609375,
      "High": 7186.830078125,
      "Low": 7151.1840820312,
      "Close": 7155.4501953125,
      "Volume": 0
    },
    {
      "Datetime": "2026-05-08T02:15:00.000Z",
      "Open": 7155.4501953125,
      "High": 7165.5,
      "Low": 7150.0,
      "Close": 7160.25,
      "Volume": 0
    }
  ],
  "count": 50,
  "timestamp": "2026-05-06T10:30:00.123456",
  "cached": false
}
```

**Important Notes:**
- **Intraday (1m, 5m, 15m, 1h) requires period >= 2d** for most indices
- ^JKSE doesn't support period=1d with intraday intervals
- Use `period=2d&interval=15m` for recent intraday data
- Daily intervals (1d, 1wk, 1mo) work with any period

**Error Scenarios:**
```json
{
  "error": "^JKSE does not support 1m interval with period=1d",
  "status": "failed",
  "suggestion": "Try: /index/^JKSE/history?period=2d&interval=1m (minimum period for intraday is 2d)",
  "timestamp": "2026-05-06T10:30:00.123456"
}
```

**Usage Notes:**
- Intraday data (1m, 5m, 15m, 1h) requires period >= 2d for most indices
- ^JKSE doesn't support period=1d with intraday intervals  
- Use period=2d or higher for intraday data
- Daily/weekly/monthly intervals work with any period

---

## 9. Sector Performance Summary

**Purpose:** Get today's performance summary for all market sectors, showing which sectors are up or down

**Endpoint:** `GET /sectors/summary`

**Query Parameters:**

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `region` | string | "id" | No | Market region (e.g., "id" for Indonesia, "us" for USA) |

**Example Request:**
```bash
GET /sectors/summary?region=id
```

**Response:**
```json
{
  "sectors": [
    {
      "name": "Healthcare",
      "key": "healthcare",
      "displayName": "HEALTH",
      "change_percent": 2.44,
      "stock_count": 38,
      "direction": "up"
    },
    {
      "name": "Industrials",
      "key": "industrials",
      "displayName": "INDUSTRIAL",
      "change_percent": 0.97,
      "stock_count": 100,
      "direction": "up"
    },
    {
      "name": "Consumer Defensive",
      "key": "consumer-defensive",
      "displayName": "NON-CYCLICAL",
      "change_percent": 0.96,
      "stock_count": 100,
      "direction": "up"
    },
    {
      "name": "Energy",
      "key": "energy",
      "displayName": "ENERGY",
      "change_percent": -1.53,
      "stock_count": 56,
      "direction": "down"
    }
  ],
  "count": 11,
  "region": "id",
  "timestamp": "2026-05-11T21:38:44.123456",
  "cached": false
}
```

**Sector Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full sector name (e.g., "Financial Services") |
| `key` | string | Sector slug used in API paths (e.g., "financial-services") |
| `displayName` | string | Short uppercase label for UI display (e.g., "FINANCIAL") |
| `change_percent` | float | Average % change of all stocks in the sector today |
| `stock_count` | int | Number of stocks sampled for the average |
| `direction` | string | `"up"`, `"down"`, or `"flat"` |

**Supported Sectors:**

| Key | Name | `displayName` |
|-----|------|---------------|
| `financial-services` | Financial Services | `FINANCIAL` |
| `energy` | Energy | `ENERGY` |
| `technology` | Technology | `TECHNOLOGY` |
| `basic-materials` | Basic Materials | `MATERIAL` |
| `consumer-cyclical` | Consumer Cyclical | `CYCLICAL` |
| `consumer-defensive` | Consumer Defensive | `NON-CYCLICAL` |
| `healthcare` | Healthcare | `HEALTH` |
| `industrials` | Industrials | `INDUSTRIAL` |
| `real-estate` | Real Estate | `PROPERTY` |
| `utilities` | Utilities | `UTILITY` |
| `communication-services` | Communication Services | `TELECOM` |

**How It Works:**
- For each sector, runs a `yf.screen()` query filtered by `region` + `sector`
- Aggregates the average `regularMarketChangePercent` across up to 100 stocks per sector
- Returns sectors sorted from best to worst performer (descending `change_percent`)
- Sectors with no stocks in the given region are excluded from the result

**UI Usage Tips:**
- Display as a horizontal scrollable card list or vertical list
- Color-code by `direction`: green for `"up"`, red for `"down"`, grey for `"flat"`
- Use `displayName` as the card label (short, uppercase)
- Show `change_percent` with `+` prefix for positive values
- `stock_count` can be shown as a subtitle (e.g., "38 stocks")
- Sort is already applied server-side (best → worst performer)

**Performance Note:**
- This endpoint makes 11 upstream API calls (one per sector) — first load takes ~5-8s
- **Always use cached response when available** (`cached: true`)
- Server caches for 5 minutes; subsequent calls return instantly

**Error Response:**
```json
{
  "error": "Error description",
  "status": "failed",
  "region": "id",
  "timestamp": "2026-05-11T10:30:00.123456"
}
```

---

## 10. Sector Stocks

**Purpose:** Get all stocks/tickers belonging to a specific sector

**Endpoint:** `GET /sectors/{sector_key}/stocks`

**Path Parameters:**

| Name | Type | Required | Example | Description |
|------|------|----------|---------|-------------|
| `sector_key` | string | Yes | "financial-services" | Sector key from supported sectors list |

**Query Parameters:**

| Name | Type | Default | Required | Constraints | Description |
|------|------|---------|----------|-------------|-------------|
| `region` | string | "id" | No | 2-char code | Market region |
| `limit` | int | 50 | No | 1-100 | Number of stocks to return |

**Example Requests:**
```bash
# Get top 50 financial stocks in Indonesia
GET /sectors/financial-services/stocks?region=id&limit=50

# Get top 20 energy stocks
GET /sectors/energy/stocks?limit=20

# Get technology stocks in USA
GET /sectors/technology/stocks?region=us
```

**Response:**
```json
{
  "stocks": [
    {
      "ticker": "BBCA.JK",
      "name": "PT Bank Central Asia Tbk",
      "price": 5850.0,
      "change_value": 150.0,
      "change_percent": 2.50,
      "volume": 303405400,
      "market_cap": 718825993535488
    },
    {
      "ticker": "BMRI.JK",
      "name": "PT Bank Mandiri (Persero) Tbk",
      "price": 5200.0,
      "change_value": -50.0,
      "change_percent": -0.95,
      "volume": 89123400,
      "market_cap": 485123456789012
    }
  ],
  "count": 50,
  "sector": {
    "name": "Financial Services",
    "key": "financial-services",
    "displayName": "FINANCIAL"
  },
  "region": "id",
  "timestamp": "2026-05-11T10:30:00.123456",
  "cached": false
}
```

**Stock Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock symbol |
| `name` | string | Company short name |
| `price` | float | Current market price |
| `change_value` | float | Absolute price change today |
| `change_percent` | float | Percentage price change today |
| `volume` | int | Today's trading volume |
| `market_cap` | int | Market capitalization |

**Sector Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full sector name |
| `key` | string | Sector slug |
| `displayName` | string | Short uppercase UI label |

**Invalid Sector Key Error:**
```json
{
  "error": "Unknown sector key: 'banking'",
  "status": "failed",
  "supported_keys": ["financial-services", "energy", "technology", "basic-materials", "consumer-cyclical", "consumer-defensive", "healthcare", "industrials", "real-estate", "utilities", "communication-services"],
  "timestamp": "2026-05-11T10:30:00.123456"
}
```

**Notes:**
- Stocks are sorted by `change_percent` descending (best performers first)
- `limit` capped at 100 max
- Shares the same `sectors_cache` as `/sectors/summary` (5-min TTL)
- Use sector `key` values from `/sectors/summary` response or the supported sectors table

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Ticker/endpoint not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |

### Error Response Format
```json
{
  "error": "Detailed error message",
  "status": "failed",
  "timestamp": "2026-05-06T10:30:00",
  "suggestion": "Try this instead..." // Optional
}
```

**Retry Strategy:**
- On 429 errors: Exponential backoff (2s, 4s, 8s, max 60s)
- On 500 errors: Retry up to 3 times
- On 400 errors: Don't retry (client error)

---

## Rate Limiting

### Server-Side
- No hard rate limits currently enforced
- Yahoo Finance underlying API: ~100-200 req/min
- Server-side caching reduces upstream calls

### Client Best Practices
1. Respect server cache TTLs (check `cached` field in response)
2. Implement exponential backoff on 429 errors
3. Batch parallel requests during initial load
4. Debounce user-triggered requests (search, refresh)

---

## Caching

### Server Cache TTLs

| Endpoint | TTL | Key |
|----------|-----|-----|
| Gainers/Losers | 5 min | `gainers_{region}_{limit}` |
| Stock Detail | 5 min | `stock_{ticker}` |
| Stock History | 5 min | `history_{ticker}_{period}_{interval}_{limit}` |
| Stock News | 30 min | `news_{ticker}_{count}_{tab}` |
| Highlighted News | 30 min | `news_highlighted_{count}_{min_id}` |
| Index History | 1 hour | `index_{symbol}_{period}_{interval}_{limit}` |
| Sectors Summary | 5 min | `sectors_{region}` |
| Sector Stocks | 5 min | `sector_stocks_{sector_key}_{region}_{limit}` |

### Cache Headers
All responses include:
- `cached`: boolean - Indicates if response came from cache
- `timestamp`: ISO 8601 datetime - Response generation time

---

## Testing

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Gainers (top 5)
curl "http://localhost:8000/stocks/gainers?limit=5"

# Losers (top 5)
curl "http://localhost:8000/stocks/losers?limit=5"

# Stock detail
curl http://localhost:8000/stocks/BBCA.JK

# Stock history (1 month, daily)
curl "http://localhost:8000/stocks/BBCA.JK/history?period=1mo&interval=1d"

# Stock news (5 items)
curl "http://localhost:8000/stocks/BBCA.JK/news?count=5"

# Highlighted market news (first page, 10 items)
curl "http://localhost:8000/news/highlighted?count=10"

# Highlighted market news (next page using min_id)
curl "http://localhost:8000/news/highlighted?count=10&min_id=1234567890"

# Index history (2 days, 15-minute intervals)
curl "http://localhost:8000/index/^JKSE/history?period=2d&interval=15m&limit=20"

# Sector summary (Indonesia)
curl "http://localhost:8000/sectors/summary?region=id"

# Sector summary (USA)
curl "http://localhost:8000/sectors/summary?region=us"

# Sector stocks - Financial Services (Indonesia, top 50)
curl "http://localhost:8000/sectors/financial-services/stocks?region=id&limit=50"

# Sector stocks - Energy (top 20)
curl "http://localhost:8000/sectors/energy/stocks?limit=20"

# Sector stocks - Technology (USA)
curl "http://localhost:8000/sectors/technology/stocks?region=us"
```

### Interactive Documentation
FastAPI provides auto-generated Swagger UI:
```
http://localhost:8000/docs
```

### Testing Checklist
- [ ] Health check returns 200 OK
- [ ] Gainers returns stocks with `change_value` and `change_percent` fields
- [ ] Losers returns stocks with `change_value` and `change_percent` fields
- [ ] Stock detail returns raw_info object
- [ ] History returns OHLCV data array
- [ ] News returns news array (or empty with message)
- [ ] Index returns data with datetime timestamps
- [ ] Sectors summary returns sectors with `displayName` field
- [ ] Sectors summary sorted by change_percent descending
- [ ] Sectors direction field is "up"/"down"/"flat"
- [ ] Sector stocks returns stocks for valid sector key
- [ ] Sector stocks returns error with `supported_keys` for invalid key
- [ ] Sector stocks response includes `sector` object with `displayName`
- [ ] Cache works (second request shows cached=true)
- [ ] Invalid ticker returns appropriate error
- [ ] Rate limiting triggers 429 when exceeded

---

## Common API Workflows

### Workflow 1: Load Home Screen
```
1. GET /stocks/gainers?limit=10
2. GET /stocks/losers?limit=10
3. GET /index/^JKSE/history?period=2d&interval=15m&limit=30
4. GET /sectors/summary?region=id

Requests 1-3 can be made in parallel. Request 4 is slower (~5-8s first load).
Total expected time: ~5-8s (first load), <500ms (cached)
```

### Workflow 2: View Stock Detail
```
1. GET /stocks/{ticker}
2. GET /stocks/{ticker}/history?period=1mo&interval=1d
3. GET /stocks/{ticker}/news?count=5

All requests can be made in parallel.
Total expected time: ~2-3s (first load), <500ms (cached)
```

### Workflow 3: Browse Sector
```
1. GET /sectors/summary?region=id          (show all sectors with performance)
2. GET /sectors/{sector_key}/stocks        (user taps a sector card)
3. GET /stocks/{ticker}                    (user taps a stock)

Sequential flow — each step depends on user selection from previous step.
```

### Workflow 4: Compare Multiple Stocks
```
1. GET /stocks/BBCA.JK
2. GET /stocks/ASII.JK
3. GET /stocks/UNVR.JK

Make requests in parallel.
Parse and display side-by-side comparison.
```

---

## Data Freshness

| Data Type | Update Frequency | Source |
|-----------|------------------|--------|
| Stock prices | Real-time (with 15min delay) | Yahoo Finance API |
| Gainers/Losers | Every 5 minutes (server cache) | Calculated from screener |
| Stock info | Daily | Yahoo Finance ticker data |
| News | Every 30 minutes | Yahoo Finance news feed |
| Index data | Real-time (market hours) | Yahoo Finance index feed |

**Market Hours (WIB):**
- Indonesia (IDX): 09:00 - 15:30 (Mon-Fri)
- Data outside market hours shows last closing values

---

## Changelog

### v1.3 (May 11, 2026)
- Added `/sectors/{sector_key}/stocks` endpoint (Section 10)
  - Returns all stocks for a given sector filtered by region
  - Supports `limit` up to 100, sorted by `change_percent` descending
  - Returns `sector` object with `name`, `key`, and `displayName`
  - Returns error with `supported_keys` list for invalid sector key
- Added `change_value` field to all stock objects (gainers, losers, sector stocks)
  - Absolute price change in local currency (sourced from `regularMarketChange`)
- Added `displayName` field to all sector objects
  - Short uppercase UI label (e.g., `FINANCIAL`, `NON-CYCLICAL`, `TELECOM`)
- Updated Quick Reference table with new endpoint
- Updated cURL examples, testing checklist, and workflows

### v1.2 (May 11, 2026)
- Added `/sectors/summary` endpoint
  - Returns today's performance for all 11 Yahoo Finance sectors
  - Sorted by `change_percent` descending (best → worst)
  - Includes `direction` field: `"up"` / `"down"` / `"flat"`
  - Supports any Yahoo Finance region code (default: `"id"`)
  - 5-minute server cache

### v1.1 (May 9, 2026)
- **Breaking Change:** Updated `/news/highlighted` endpoint
  - Removed `region` parameter (now uses Finnhub general news for all regions)
  - Added `min_id` parameter for cursor-based pagination
  - Changed source from index tickers to "finnhub"
  - Added `next_min_id` and `has_next` fields to response for pagination support
  - More reliable and comprehensive market news coverage

### v1.0 (May 6, 2026)
- Initial API specification
- 7 endpoints documented
- Complete request/response examples
- Error handling patterns
- Caching strategy defined
- Testing guidelines included

---

*API Specification | StockBit Mini App | Last Updated: May 11, 2026*
