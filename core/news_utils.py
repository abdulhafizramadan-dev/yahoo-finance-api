from datetime import datetime


def extract_news_item(raw_item: dict) -> dict:
    try:
        if not raw_item or not isinstance(raw_item, dict):
            return None

        content = raw_item.get("content")
        if not content or not isinstance(content, dict):
            return None

        provider = content.get("provider") or {}
        urls = content.get("clickThroughUrl") or {}
        thumbnail = content.get("thumbnail") or {}
        finance_obj = content.get("finance") or {}
        finance = finance_obj.get("premiumFinance", {}) if isinstance(finance_obj, dict) else {}
        metadata = content.get("metadata") or {}

        thumbnail_urls = {}
        if isinstance(thumbnail, dict) and thumbnail.get("resolutions"):
            for res in thumbnail["resolutions"]:
                if isinstance(res, dict):
                    tag = res.get("tag", "")
                    thumbnail_urls[tag] = res.get("url")

        return {
            "id": content.get("id"),
            "title": content.get("title"),
            "summary": content.get("summary"),
            "datePublished": content.get("pubDate"),
            "provider": {
                "name": provider.get("displayName") if isinstance(provider, dict) else None,
                "url": provider.get("url") if isinstance(provider, dict) else None,
            },
            "articleUrl": urls.get("url") if isinstance(urls, dict) and urls else None,
            "thumbnail": thumbnail.get("originalUrl") if isinstance(thumbnail, dict) else None,
            "thumbnails": thumbnail_urls,
            "isPremium": finance.get("isPremiumNews", False) if isinstance(finance, dict) else False,
            "isEditorsPick": metadata.get("editorsPick", False) if isinstance(metadata, dict) else False,
        }
    except Exception:
        return None


def extract_finnhub_news(raw_item: dict) -> dict:
    try:
        if not raw_item or not isinstance(raw_item, dict):
            return None

        timestamp = raw_item.get("datetime")
        date_published = None
        if timestamp:
            try:
                date_published = datetime.fromtimestamp(timestamp).isoformat() + "Z"
            except (ValueError, OSError, TypeError):
                date_published = None

        return {
            "id": raw_item.get("id"),
            "title": raw_item.get("headline"),
            "summary": raw_item.get("summary"),
            "datePublished": date_published,
            "provider": {
                "name": raw_item.get("source"),
                "url": raw_item.get("url"),
            },
            "articleUrl": raw_item.get("url"),
            "thumbnail": raw_item.get("image"),
            "thumbnails": {
                "original": raw_item.get("image"),
            },
            "isPremium": False,
            "isEditorsPick": False,
        }
    except Exception:
        return None

