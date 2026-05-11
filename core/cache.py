from datetime import datetime

cache_timestamps: dict = {}

gainers_cache: dict = {}
losers_cache: dict = {}
top_values_cache: dict = {}
top_volumes_cache: dict = {}
history_cache: dict = {}
news_cache: dict = {}
index_cache: dict = {}
news_highlighted_cache: dict = {}
sectors_cache: dict = {}


def is_cache_valid(key: str, ttl_seconds: int = 300) -> bool:
    if key not in cache_timestamps:
        return False
    elapsed = (datetime.now() - cache_timestamps[key]).total_seconds()
    return elapsed < ttl_seconds

