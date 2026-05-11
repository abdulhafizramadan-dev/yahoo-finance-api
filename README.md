# 📈 StockBit - Yahoo Finance API

**Mini Indonesia stock market app with real-time IDX (Indonesian Composite Index) data.**

A FastAPI backend for stock screening, price tracking, and market analysis using Yahoo Finance API. Designed for mobile-first development with built-in caching, light/dark mode support, and comprehensive API documentation.

**Status:** POC (Proof of Concept) | **MVP Target:** Complete by May 2026

---

## 🎯 Features

### Phase 1: MVP ⭐
- ✅ Top gainers/losers with absolute & percentage change
- ✅ Stock price history (OHLCV) with intraday support
- ✅ Market indices (IHSG/^JKSE with 1-minute charts)
- ✅ Stock news feed (via yfinance)
- ✅ Highlighted market news (via Finnhub, with pagination)
- ✅ Sector performance summary (11 sectors)
- ✅ Sector stock listing (browse stocks by sector)
- ✅ Health check endpoint

### Phase 2: Engagement 📲
- 🔄 Watchlist management
- 🔄 Portfolio tracker
- 🔄 Compare stocks

### Phase 3: Growth 🚀
- ⏳ Price alerts
- ⏳ Technical indicators
- ⏳ AI recommendations

---

## 🏗️ Architecture

```
yahoo-finance-api/
├── app.py                    # Entry point — FastAPI init + router registration
├── config.py                 # Constants: ALLOWED_ORIGINS, YAHOO_SECTORS, Finnhub client
├── requirements.txt          # Python dependencies
│
├── core/                     # Shared utilities (reusable across routers)
│   ├── cache.py              # Cache dicts + is_cache_valid()
│   ├── utils.py              # serialize_value(), safe_num()
│   └── news_utils.py         # extract_news_item(), extract_finnhub_news()
│
├── routers/                  # Endpoint handlers (one file per domain)
│   ├── stocks.py             # /stocks/* (gainers, losers, history, news, detail)
│   ├── news.py               # /news/highlighted
│   ├── index.py              # /index/{symbol}/history
│   └── sectors.py            # /sectors/summary, /sectors/{key}/stocks
│
├── API_SPEC.md               # Full API documentation (v1.3)
```

### Technology Stack
- **Framework:** FastAPI (Python)
- **Data Source:** Yahoo Finance (yfinance) + Finnhub (news)
- **Caching:** In-memory per-router (add Redis for production)
- **Deployment:** Render.com / Railway

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or poetry
- Finnhub API key (free at [finnhub.io](https://finnhub.io/register))

### Installation

```bash
# Clone or navigate to project
cd yahoo-finance-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "FINNHUB_API_KEY=your_key_here" > .env
```

### Running Locally

```bash
# Development
python app.py

# Uvicorn with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc:      http://localhost:8000/redoc
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Top gainers
curl "http://localhost:8000/stocks/gainers?limit=10"

# Top losers
curl "http://localhost:8000/stocks/losers?limit=10"

# Stock history (for charts)
curl "http://localhost:8000/stocks/BBCA.JK/history?period=1mo&interval=1d"

# Market index (IHSG intraday)
curl "http://localhost:8000/index/^JKSE/history?period=2d&interval=15m&limit=30"

# Stock news
curl "http://localhost:8000/stocks/BBCA.JK/news?count=10"

# Highlighted market news
curl "http://localhost:8000/news/highlighted?count=10"

# Sector performance summary
curl "http://localhost:8000/sectors/summary?region=id"

# Stocks in a specific sector
curl "http://localhost:8000/sectors/financial-services/stocks?region=id&limit=20"
```

---

## 📚 API Documentation

### Quick Reference

| Endpoint | Method | Purpose | Cache |
|----------|--------|---------|-------|
| `/health` | GET | API status | N/A |
| `/stocks/gainers` | GET | Top gaining stocks | 5 min |
| `/stocks/losers` | GET | Top losing stocks | 5 min |
| `/stocks/{ticker}` | GET | Stock details (raw_info) | 5 min |
| `/stocks/{ticker}/history` | GET | Price history (OHLCV) | 5 min |
| `/stocks/{ticker}/news` | GET | Stock news feed | 30 min |
| `/news/highlighted` | GET | General market news (Finnhub) | 30 min |
| `/index/{symbol}/history` | GET | Market index OHLCV | 1 hour |
| `/sectors/summary` | GET | All sectors % change today | 5 min |
| `/sectors/{sector_key}/stocks` | GET | Stocks in a sector | 5 min |

**Full API Spec:** See `API_SPEC.md` (v1.3, detailed contracts)

### Example Request/Response

```bash
# Request
GET /stocks/gainers?limit=5
```

```json
{
  "stocks": [
    {
      "ticker": "RMKE.JK",
      "name": "RMK Energy Tbk.",
      "price": 3370.0,
      "change_value": 200.0,
      "change_percent": 6.31,
      "volume": 30017300,
      "market_cap": 14743750311936
    }
  ],
  "count": 5,
  "region": "id",
  "timestamp": "2026-05-11T10:30:00.123456",
  "cached": false
}
```

```bash
# Request
GET /sectors/summary?region=id
```

```json
{
  "sectors": [
    { "name": "Healthcare", "key": "healthcare", "displayName": "HEALTH", "change_percent": 2.44, "stock_count": 38, "direction": "up" },
    { "name": "Industrials", "key": "industrials", "displayName": "INDUSTRIAL", "change_percent": 0.97, "stock_count": 100, "direction": "up" },
    { "name": "Energy", "key": "energy", "displayName": "ENERGY", "change_percent": -1.53, "stock_count": 56, "direction": "down" }
  ],
  "count": 11,
  "region": "id",
  "cached": false
}
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (not committed to repo):

```env
FINNHUB_API_KEY=your_finnhub_api_key_here
```

Get a free key at [finnhub.io/register](https://finnhub.io/register) (60 req/min free tier).

### Caching Strategy

**Current (Development):**
- In-memory cache per router module
- Lost on server restart
- TTL per endpoint type:

| Endpoint | TTL |
|----------|-----|
| Gainers / Losers | 5 min |
| Stock History | 5 min |
| Sectors Summary / Stocks | 5 min |
| Stock / Market News | 30 min |
| Index History | 1 hour |

**Recommended (Production):**
- Migrate to Redis for distributed cache
- Add `pip install redis` and update `core/cache.py`

---

## 📱 Frontend Integration

### Supported Regions
- `id` - Indonesia (default)
- `us` - United States
- `jp` - Japan
- Any Yahoo Finance region code

### Common Data Patterns

**Home Screen (parallel requests):**
```bash
GET /stocks/gainers?limit=10
GET /stocks/losers?limit=10
GET /index/^JKSE/history?period=2d&interval=15m&limit=30
GET /sectors/summary?region=id
```

**Stock Detail Screen (parallel requests):**
```bash
GET /stocks/{ticker}
GET /stocks/{ticker}/history?period=1mo&interval=1d
GET /stocks/{ticker}/news?count=10
```

**Sector Browse Flow (sequential):**
```bash
GET /sectors/summary?region=id           # User sees sector cards
GET /sectors/{sector_key}/stocks         # User taps a sector
GET /stocks/{ticker}                     # User taps a stock
```

**News Feed with Pagination:**
```bash
GET /news/highlighted?count=10           # First page
GET /news/highlighted?count=10&min_id=X  # Next page (use next_min_id from response)
```

---

## ⚡ Performance Notes

### Rate Limits
- **yfinance:** ~10-20 req/min (may get blocked)
- **Finnhub (free tier):** ~60 req/min
- **Recommended:** Use caching + reasonable request intervals

### Optimization Tips
1. **Cache aggressively** — Most users want slightly delayed data
2. **Batch requests** — Load multiple endpoints in parallel
3. **`/sectors/summary` is slow** — Makes 11 upstream calls on first load (~5-8s). Always rely on cache after first hit.
4. **Pagination** — Use `min_id` for news, `limit` for stock lists

### Known Issues
- **429 Errors:** Yahoo Finance rate limiting. Use exponential backoff
- **Empty data:** Market might be closed or invalid ticker
- **Intraday index data:** `^JKSE` requires `period≥2d` (use `period=2d&interval=15m`)

---

## 🛠️ Development Workflow

### Adding a New Endpoint

1. **Decide which router** the endpoint belongs to (`routers/stocks.py`, `routers/sectors.py`, etc.)
2. **Add a cache dict** in `core/cache.py` if needed
3. **Write the handler** in the appropriate router file using existing patterns
4. **Register** via `app.include_router()` in `app.py` (already done for existing routers)
5. **Test via `/docs`** Swagger UI

### Example Pattern (inside any router file)

```python
from core.cache import my_cache, cache_timestamps, is_cache_valid

@router.get("/example")
def api_example(param: str = "default"):
    cache_key = f"example_{param}"

    if cache_key in my_cache and is_cache_valid(cache_key):
        cached = my_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        result = yf.screen(...)  # your logic
        response = {"data": result, "cached": False, "timestamp": datetime.now().isoformat()}
        my_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}
```

### Adding a New Sector / Index

- **New sector:** Add entry to `YAHOO_SECTORS` in `config.py` — all routers pick it up automatically
- **New index:** Add entry to `INDEX_INFO_MAP` and `SUPPORTED_INDICES` in `config.py`

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip install -r requirements.txt
```

### "FINNHUB_API_KEY environment variable is required"
```bash
echo "FINNHUB_API_KEY=your_key_here" > .env
```

### "429 Too Many Requests"
- Server-side cache already handles most cases
- Reduce request frequency
- Add exponential backoff on the client

### "No data available for ticker"
- Verify market hours: 09:00–15:30 WIB for IDX
- Check ticker format: use `BBCA.JK` not `BBCA`
- Try a different period

### Chart data is empty for index
- Use `period=2d` minimum for intraday (`1m`, `5m`, `15m`, `1h`) on `^JKSE`

---

## 🚦 Deployment

### Render.com (Recommended for MVP)
1. Connect GitHub repo
2. Set start command: `uvicorn app:app --host 0.0.0.0 --port 8000`
3. Add environment variable: `FINNHUB_API_KEY=your_key`
4. Deploy

**Health Check URL:** `https://your-app.onrender.com/health`

---

## 📋 Checklist Before Launch

- [ ] Health endpoint working
- [ ] Gainers/Losers returning data with `change_value`
- [ ] Index chart (^JKSE) working with `period=2d`
- [ ] Stock news fetching data
- [ ] Highlighted news (Finnhub) fetching with pagination
- [ ] Sectors summary returning all 11 sectors
- [ ] Sector stocks returning correct stocks for a key
- [ ] Cache working (second request shows `cached: true`)
- [ ] Error handling for invalid ticker/sector key
- [ ] CORS enabled for frontend domain
- [ ] Deployed to Render/Railway
- [ ] API docs accessible at `/docs`

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `API_SPEC.md` | Complete API reference (v1.3, 10 endpoints) |
| `FIGMA_DESIGN_SPEC.md` | Mobile UI/UX specification |
| `APP_STRATEGY.md` | Product roadmap |
| `AGENTS.md` | AI agent developer guide |

---

## 📊 Quick Stats

- **API Endpoints:** 10
- **Supported Indices:** 10
- **Supported Sectors:** 11
- **Regions Supported:** Any Yahoo Finance region code
- **News Sources:** Yahoo Finance + Finnhub
- **Cache Layers:** Per-router in-memory (5 dicts)
- **Response Time:** <500ms (cached), ~1–3s (uncached), ~5–8s (sectors/summary first load)

---

**Built with ❤️ for the Indonesian stock market community.**

*Last Updated: May 11, 2026*
