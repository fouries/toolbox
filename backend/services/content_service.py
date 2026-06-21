from typing import Any, Callable, Dict

from api.tianapi import TianApiService
from utils.cache import cache, make_cache_key


class ContentService:
    """内容聚合服务层：对上屏接口做二级缓存，隔离 API 层与第三方服务细节。"""

    @staticmethod
    async def _cached_result(key_prefix: str, ttl: int, producer: Callable[[], Any], **params) -> Dict[str, Any]:
        cache_key = make_cache_key(key_prefix, **params)
        cached = await cache.get(cache_key)
        if isinstance(cached, dict):
            cached["from_cache"] = True
            return cached
        result = await producer()
        if isinstance(result, dict) and int(result.get("code", 200)) == 200:
            await cache.set(cache_key, result, ttl=ttl)
        return result

    @classmethod
    async def get_info_news(cls, category: str = "internet") -> Dict[str, Any]:
        return await cls._cached_result(
            "svc:news",
            300,
            lambda: TianApiService.get_info_news(category),
            category=category,
            version="v1",
        )

    @classmethod
    async def get_daily_brief(cls) -> Dict[str, Any]:
        return await cls._cached_result(
            "svc:daily_brief",
            900,
            TianApiService.get_daily_brief,
            version="v1",
        )

    @classmethod
    async def get_hot_search(cls, platform: str = "baidu") -> Dict[str, Any]:
        return await cls._cached_result(
            "svc:hot_search",
            180,
            lambda: TianApiService.get_hot_search(platform),
            platform=platform,
            version="v1",
        )

    @classmethod
    async def get_hot_search_detail(cls, platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = "") -> Dict[str, Any]:
        return await cls._cached_result(
            "svc:hot_search_detail",
            600,
            lambda: TianApiService.get_hot_search_detail(platform, keyword, hot, description, url, raw),
            platform=platform,
            keyword=keyword,
            hot=hot,
            description=description,
            url=url,
            raw=raw,
            version="v1",
        )
