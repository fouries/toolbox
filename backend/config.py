# 配置文件
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 天行数据 API Key (https://www.tianapi.com)
    TIANAPI_KEY: str = ""
    
    # Redis 配置（用于缓存，降低API调用成本）
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = True  # 生产环境建议使用，开发环境可以设为 False 使用内存缓存
    
    # 默认缓存TTL（秒）
    CACHE_TTL_DEFAULT: int = 300  # 5分钟
    CACHE_TTL_OIL: int = 3600  # 油价1小时
    CACHE_TTL_WEATHER: int = 1800  # 天气30分钟
    
    # API配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
