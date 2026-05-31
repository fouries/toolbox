# 配置文件
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 天行数据 API Key (https://www.tianapi.com)
    TIANAPI_KEY: str = ""
    
    # Redis 配置（用于缓存，降低API调用成本）
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 缓存时间（秒）
    CACHE_TTL_OIL: int = 3600 * 12  # 油价缓存12小时
    CACHE_TTL_WEATHER: int = 3600 * 3  # 天气缓存3小时
    CACHE_TTL_DEFAULT: int = 300  # 默认缓存5分钟
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
