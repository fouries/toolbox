import json
import hashlib
from typing import Any, Optional
import redis.asyncio as redis
from config import get_settings

settings = get_settings()

class Cache:
    _instance: Optional['Cache'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_redis'):
            self._redis: Optional[redis.Redis] = None
    
    async def init(self):
        """初始化Redis连接"""
        try:
            self._redis = redis.from_url(settings.REDIS_URL)
            await self._redis.ping()
            print("✅ Redis 缓存已连接")
        except Exception as e:
            print(f"⚠️ Redis 连接失败，将不使用缓存: {e}")
            self._redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._redis:
            return None
        
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        if not self._redis:
            return
        
        try:
            await self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception:
            pass
    
    async def delete(self, key: str):
        """删除缓存"""
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
        except Exception:
            pass

def make_cache_key(prefix: str, **kwargs) -> str:
    """生成缓存键"""
    sorted_params = sorted(kwargs.items())
    params_str = "&".join([f"{k}={v}" for k, v in sorted_params])
    hash_str = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{prefix}:{hash_str}"

# 全局缓存实例
cache = Cache()
