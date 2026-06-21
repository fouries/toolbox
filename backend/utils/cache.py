import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class Cache:
    _instance: Optional['Cache'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_redis'):
            self._redis: Optional[redis.Redis] = None
            self.enabled = False

    async def init(self):
        """初始化 Redis 连接。连接失败时自动降级为无缓存。"""
        redis_url = str(settings.REDIS_URL or "").strip()
        if not redis_url:
            logger.warning("redis_disabled reason=empty_url")
            self._redis = None
            self.enabled = False
            return
        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            self.enabled = True
            logger.info("redis_connected")
        except Exception as exc:
            logger.warning("redis_connect_failed fallback=no_cache error=%s", exc)
            self._redis = None
            self.enabled = False

    async def close(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            self.enabled = False

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._redis:
            return None
        try:
            data = await self._redis.get(key)
            if data:
                logger.debug("cache_hit key=%s", key)
                return json.loads(data)
        except Exception as exc:
            logger.warning("cache_get_failed key=%s error=%s", key, exc)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        if not self._redis:
            return
        try:
            await self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
        except Exception as exc:
            logger.warning("cache_set_failed key=%s error=%s", key, exc)

    async def delete(self, key: str):
        """删除缓存"""
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
        except Exception as exc:
            logger.warning("cache_delete_failed key=%s error=%s", key, exc)


def make_cache_key(prefix: str, **kwargs) -> str:
    """生成缓存键"""
    import hashlib

    sorted_params = sorted(kwargs.items())
    params_str = "&".join([f"{k}={v}" for k, v in sorted_params])
    hash_str = hashlib.md5(params_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_str}"


# 全局缓存实例
cache = Cache()
