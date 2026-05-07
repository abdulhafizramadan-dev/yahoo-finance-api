# 📈 StockBit - Yahoo Finance API

**Mini Indonesia stock market app with real-time IDX (Indonesian Composite Index) data.**

A FastAPI backend for stock screening, price tracking, and market analysis using Yahoo Finance API. Designed for mobile-first development with built-in caching, light/dark mode support, and comprehensive API documentation.

**Status:** POC (Proof of Concept) | **MVP Target:** Complete by May 2026

---

## 🎯 Features

### Phase 1: MVP ⭐
- ✅ Top gainers/losers
- ✅ Stock price history (OHLCV) with intraday support
- ✅ Market indices (IHSG/^JKSE with 1-minute charts)
- ✅ Stock news feed
- ✅ Search functionality
- ✅ Health check endpoint

### Phase 2: Engagement 📲
- 🔄 Watchlist management
- 🔄 Portfolio tracker
- 🔄 Sector-based screening
- 🔄 Compare stocks

### Phase 3: Growth 🚀
- ⏳ Price alerts
- ⏳ Technical indicators
- ⏳ AI recommendations

---

## 🏗️ Architecture

```
yahoo-finance-api/
├── app.py                    # FastAPI application (primary)
├── screener.py              # Fallback: Direct Yahoo API via curl_cffi
├── API_SPEC.md              # API documentation for developers
├── requirements.txt         # Python dependencies
```

### Technology Stack
- **Framework:** FastAPI (Python)
- **Data Source:** Yahoo Finance API (via yfinance)
- **Caching:** In-memory (add Redis for production)
- **HTTP Client:** yfinance + optional curl_cffi (TLS fingerprinting)
- **Deployment:** Render.com / Railway

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or poetry
- (Optional) Redis for production caching

### Installation

```bash
# Clone or navigate to project
cd yahoo-finance-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Development
python app.py

# Uvicorn with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Access API docs
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
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

# Market index (IHSG)
curl "http://localhost:8000/index/^JKSE/history?period=1d&interval=15m&limit=30"

# Stock news
curl "http://localhost:8000/stocks/BBCA.JK/news?count=10"
```

---

## 📚 API Documentation

### Quick Reference

| Endpoint | Method | Purpose | Cache |
|----------|--------|---------|-------|
| `/health` | GET | API status | N/A |
| `/stocks/gainers` | GET | Top gaining stocks | 5 min |
| `/stocks/losers` | GET | Top losing stocks | 5 min |
| `/stocks/{ticker}` | GET | Stock details | 5 min |
| `/stocks/{ticker}/history` | GET | Price history (OHLCV) | 5 min |
| `/stocks/{ticker}/news` | GET | News feed | 30 min |
| `/index/{symbol}/history` | GET | Market indices | 1 hour |

**Full API Spec:** See `API_SPEC.md` (883 lines, detailed contracts)

### Example Request/Response

```bash
# Request
GET /stocks/gainers?limit=5

# Response
{
  "stocks": [
    {
      "ticker": "BBCA.JK",
      "name": "PT Bank Central Asia Tbk",
      "price": 5850.0,
      "change_percent": 2.50,
      "volume": 303405400,
      "market_cap": 718825993535488
    }
  ],
  "count": 5,
  "region": "id",
  "timestamp": "2026-05-07T10:30:00.123456",
  "cached": false
}
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (not included in repo for security):

```env
# Development
API_ENV=development
BASE_URL=http://localhost:8000

# Production
API_ENV=production
BASE_URL=https://your-api.onrender.com

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Cache (optional for production)
REDIS_URL=redis://localhost:6379
```

### Caching Strategy

**Current (Development):**
- In-memory cache only
- Lost on server restart
- TTL per endpoint:
  - Gainers/Losers: 5 min
  - History: 5 min
  - News: 30 min
  - Indices: 1 hour

**Recommended (Production):**
- Use Redis for distributed cache
- Add cache layer: `pip install redis`
- Update cache logic in `app.py`

---

## 📱 Frontend Integration

### Supported Regions
- `id` - Indonesia (default)
- `us` - United States
- `jp` - Japan
- (See `APP_STRATEGY.md` for full list)

### Common Data Patterns

**Home Screen:**
```python
# Load in parallel
gainers = GET /stocks/gainers?limit=10
losers = GET /stocks/losers?limit=10
index = GET /index/^JKSE/history?period=1d&interval=15m&limit=30
```

**Stock Detail Screen:**
```python
info = GET /stocks/{ticker}
history = GET /stocks/{ticker}/history?period=1mo&interval=1d
news = GET /stocks/{ticker}/news?count=10
```

---

## ⚡ Performance Notes

### Rate Limits
- **yfinance:** ~10-20 req/min (may get blocked)
- **curl_cffi (screener.py):** ~100-200 req/min (TLS fingerprinting)
- **Recommended:** Use caching + reasonable request intervals

### Optimization Tips
1. **Cache aggressively** - Most users want slightly delayed data
2. **Batch requests** - Load multiple endpoints in parallel
3. **Pagination** - Show 10 items initially, lazy load more
4. **Preload on launch** - Fetch data while splash screen visible

### Known Issues
- **429 Errors:** Yahoo Finance rate limiting. Use exponential backoff
- **Empty data:** Market might be closed or invalid ticker
- **Intraday data:** ^JKSE requires period≥2d (use `period=2d&interval=15m`)

---

## 🎨 Design & UI

### Figma Design
- **File:** `FIGMA_DESIGN_SPEC.md`
- **Platform:** Android (Jetpack Compose + Material Design 3)
- **Modes:** Light & Dark (automatic switching)
- **Components:** Pre-designed for all screens

### Screens
1. **Home** - Gainers, Losers, Index chart
2. **Stock Detail** - Info, chart, news feed
3. **Search** - Quick stock lookup
4. **Watchlist** - Saved stocks
5. **Settings** - Theme toggle

---

## 📖 Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `API_SPEC.md` | Complete API reference | 883 lines |
| `FIGMA_DESIGN_SPEC.md` | UI/UX specifications | 751 lines |
| `APP_STRATEGY.md` | Product roadmap | 825 lines |
| `AGENTS.md` | AI agent guide | 40 lines |
| `DEPLOYMENT.md` | Render deployment | (if exists) |

---

## 🚦 Deployment

### Local Development
```bash
python app.py
```

### Render.com (Recommended for MVP)
1. Connect GitHub repo
2. Set start command: `uvicorn app:app --host 0.0.0.0 --port 8000`
3. Add environment variables (if using .env)
4. Deploy

**Health Check URL:** `https://your-app.onrender.com/health`

### Railway / AWS / DigitalOcean
- Similar setup (see `DEPLOYMENT.md` if available)
- Just need Python 3.9+ and pip

---

## 🔄 Development Workflow

### Adding New Endpoint

1. **Create handler function** in `app.py`
2. **Add cache dict** at top: `new_cache = {}`
3. **Check cache** before fetching
4. **Call yfinance API**
5. **Store in cache** with timestamp
6. **Return response** in standardized format
7. **Test via `/docs`** Swagger UI

### Example Pattern
```python
@app.get("/stocks/example")
def api_example(param: str = "default"):
    cache_key = f"example_{param}"
    
    if cache_key in example_cache and is_cache_valid(cache_key):
        cached = example_cache[cache_key].copy()
        cached["cached"] = True
        return cached
    
    try:
        result = yf.screen(...)  # Your logic
        response = {"data": result, "cached": False}
        example_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed"}
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip install yfinance
pip install -r requirements.txt
```

### "429 Too Many Requests"
- Use server-side cache (already implemented)
- Reduce request frequency
- Switch to `screener.py` for higher limits
- Add exponential backoff

### "No data available for ticker"
- Check if market is open (9:00-15:30 WIB for IDX)
- Verify ticker format (e.g., `BBCA.JK` not `BBCA`)
- Try different ticker or region

### Chart data is empty
- For intraday: use `period=2d` or higher
- For daily: use `period=5d` or higher
- Check if data exists for that ticker/period

---

## 📋 Checklist Before Launch

- [ ] Health endpoint working
- [ ] Gainers/Losers returning data
- [ ] Index chart (^JKSE) working
- [ ] Stock news fetching data
- [ ] Cache working (5-30 min TTL)
- [ ] Error handling for all scenarios
- [ ] CORS enabled for frontend domain
- [ ] Rate limiting handled gracefully
- [ ] Deployed to Render/Railway
- [ ] API docs accessible (`/docs`)

---

## 🤝 Contributing

### To Add Features
1. Create feature branch: `git checkout -b feature/new-endpoint`
2. Update `API_SPEC.md` first (API-first design)
3. Implement in `app.py`
4. Test via `/docs`
5. Update this README if needed
6. Commit with clear message

### Stack for Pull Requests
- Branch name: `feature/short-description`
- Commit message: `Add {feature} endpoint`
- Include API changes in PR description

---

## 📞 Support & Contact

- **API Issues:** Check `API_SPEC.md` for contract details
- **Design Questions:** See `FIGMA_DESIGN_SPEC.md`
- **Feature Ideas:** Reference `APP_STRATEGY.md`
- **Deployment Help:** Review `DEPLOYMENT.md`

---

## 📝 License

This project is for educational and commercial use. Ensure compliance with Yahoo Finance Terms of Service.

---

## 🎯 Roadmap

### Current Status (May 2026)
✅ MVP complete (7 endpoints)  
✅ Caching implemented  
✅ Index history with intraday support  
✅ News integration  

### Next (Phase 2)
🔄 Multi-region support  
🔄 Watchlist backend  
🔄 Portfolio tracker  
🔄 News search/filtering  

### Future (Phase 3)
⏳ Price alerts  
⏳ Technical indicators  
⏳ Social features  
⏳ AI recommendations  

---

## 📊 Quick Stats

- **API Endpoints:** 7
- **Supported Indices:** 10+
- **Regions Supported:** 10+
- **Cache Layers:** 3 (in-memory)
- **Response Time:** <500ms (cached), ~1-2s (uncached)
- **Uptime Target:** 99%

---

**Built with ❤️ for the Indonesian stock market community.**

*Last Updated: May 7, 2026*

