from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from config import get_settings
from utils.cache import cache
from api.tianapi import TianApiService
from api.tools import ToolsService

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时：初始化缓存
    await cache.init()
    yield
    # 关闭时：清理资源
    pass

app = FastAPI(
    title="小巧的工具箱 API",
    description="多合一工具聚合服务，支持油价、天气等查询",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": f"服务器内部错误: {str(exc)}"}
    )

# ==================== 天行数据 API ====================

@app.get("/api/oil-price", summary="油价查询", tags=["天行数据"])
async def oil_price(province: str = "北京"):
    """查询各省份油价"""
    result = await TianApiService.get_oil_price(province)
    return result

@app.get("/api/weather", summary="天气预报", tags=["天行数据"])
async def weather(city: str = "北京"):
    """查询城市天气"""
    result = await TianApiService.get_weather(city)
    return result

@app.get("/api/calendar", summary="黄历日历", tags=["天行数据"])
async def calendar(date: str = None):
    """黄历/日历查询"""
    result = await TianApiService.get_calendar(date)
    return result

# ==================== 本地工具 API ====================

@app.get("/api/qrcode", summary="二维码生成", tags=["本地工具"])
async def generate_qrcode(text: str, size: int = 256):
    """生成二维码图片（base64格式）"""
    result = ToolsService.generate_qrcode(text, size)
    return result

@app.get("/api/password", summary="随机密码", tags=["本地工具"])
async def generate_password(length: int = 16, 
                           upper: bool = True,
                           lower: bool = True,
                           number: bool = True,
                           symbol: bool = True):
    """生成随机密码"""
    result = ToolsService.generate_password(length, upper, lower, number, symbol)
    return result

@app.get("/api/base64/encode", summary="Base64编码", tags=["编码工具"])
async def base64_encode(text: str):
    """Base64编码"""
    result = ToolsService.base64_encode(text)
    return result

@app.get("/api/base64/decode", summary="Base64解码", tags=["编码工具"])
async def base64_decode(encoded: str):
    """Base64解码"""
    result = ToolsService.base64_decode(encoded)
    return result

@app.get("/api/url/encode", summary="URL编码", tags=["编码工具"])
async def url_encode(text: str):
    """URL编码"""
    result = ToolsService.url_encode(text)
    return result

@app.get("/api/url/decode", summary="URL解码", tags=["编码工具"])
async def url_decode(encoded: str):
    """URL解码"""
    result = ToolsService.url_decode(encoded)
    return result

@app.post("/api/json/format", summary="JSON格式化", tags=["编码工具"])
async def json_format(json_str: str, indent: int = 2):
    """JSON格式化"""
    result = ToolsService.json_format(json_str, indent)
    return result

# ==================== 通用接口 ====================

@app.get("/", summary="API首页")
async def root():
    return {
        "name": "小巧的工具箱 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "apis": {
            "天行数据": ["/api/oil-price", "/api/weather", "/api/calendar"],
            "本地工具": ["/api/qrcode", "/api/password"],
            "编码工具": ["/api/base64/encode", "/api/base64/decode", "/api/url/encode", "/api/url/decode", "/api/json/format"]
        }
    }

@app.get("/health", summary="健康检查")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
