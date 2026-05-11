from datetime import datetime

from fastapi import APIRouter

from config import finnhub_client
from core.cache import news_highlighted_cache, cache_timestamps, is_cache_valid
from core.news_utils import extract_finnhub_news

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/highlighted")
def api_news_highlighted(count: int = 10, min_id: int = 0):
    if count > 50:
        count = 50
    if count < 1:
        count = 10
    if min_id < 0:
        min_id = 0

    cache_key = f"news_highlighted_{count}_{min_id}"
    if cache_key in news_highlighted_cache and is_cache_valid(cache_key, ttl_seconds=1800):
        cached = news_highlighted_cache[cache_key].copy()
        cached["cached"] = True
        return cached

    try:
        news_list = []
        last_item_id = 0

        raw_news = finnhub_client.general_news('general', min_id=min_id)
        if raw_news:
            for item in raw_news:
                if isinstance(item, dict):
                    extracted = extract_finnhub_news(item)
                    if extracted:
                        news_list.append(extracted)
                    if "id" in item:
                        last_item_id = item.get("id", 0)

        paginated_news = news_list[:count]

        if not paginated_news:
            response = {
                "news": [], "count": 0, "source": "finnhub",
                "message": "No highlighted news available",
                "timestamp": datetime.now().isoformat(), "cached": False,
            }
            news_highlighted_cache[cache_key] = response
            cache_timestamps[cache_key] = datetime.now()
            return response

        response = {
            "news": paginated_news,
            "count": len(paginated_news),
            "next_min_id": last_item_id if len(news_list) >= count else 0,
            "has_next": len(news_list) >= count,
            "source": "finnhub",
            "timestamp": datetime.now().isoformat(),
            "cached": False,
        }
        news_highlighted_cache[cache_key] = response
        cache_timestamps[cache_key] = datetime.now()
        return response
    except Exception as e:
        return {"error": str(e), "status": "failed", "timestamp": datetime.now().isoformat()}

