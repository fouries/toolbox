# 配置文件
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。生产环境通过 backend/.env 或系统环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 天行数据 API Key (https://www.tianapi.com)
    TIANAPI_KEY: str = ""

    # 数据库配置：默认 SQLite；生产可通过 DATABASE_URL 切换到 MySQL 或 PostgreSQL。
    DATABASE_URL: str = "sqlite:///./data/toolbox.db"
    DB_ECHO: bool = False

    # Redis 配置（用于缓存，降低 API 调用成本）。为空时自动跳过 Redis。
    REDIS_URL: str = ""

    # 微信小程序订阅消息配置。Template ID 不是密钥，但 AppSecret 必须只放环境变量/.env。
    WECHAT_MINI_APP_ID: str = ""
    WECHAT_MINI_APP_SECRET: str = ""
    WECHAT_SUBSCRIBE_ENABLED: bool = True
    WECHAT_SUBSCRIBE_TEMPLATE_DAILY_BRIEF: str = ""
    WECHAT_SUBSCRIBE_TEMPLATE_WEATHER: str = ""
    WECHAT_SUBSCRIBE_TEMPLATE_HOT_SEARCH: str = ""
    WECHAT_SUBSCRIBE_TEMPLATE_GOLD_PRICE: str = ""
    WECHAT_SUBSCRIBE_TEMPLATE_DATA_KEYS: str = "thing1,time2,thing3"

    # 管理后台密钥，仅用于反馈后台等轻量管理接口；生产环境必须设置强随机值。
    ADMIN_KEY: str = ""

    # 缓存时间（秒）
    CACHE_TTL_OIL: int = 3600
    CACHE_TTL_WEATHER: int = 1800
    CACHE_TTL_DEFAULT: int = 300

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS 配置，环境变量支持逗号分隔字符串。
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    SLOW_REQUEST_MS: int = 1500

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache()
def get_settings():
    return Settings()
