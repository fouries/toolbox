from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio

from config import get_settings
from utils.cache import cache
from api.tianapi import TianApiService
from api.news_detail import NewsDetailService
from api.tools import ToolsService
from api.location import LocationService
from api.tool_stats import get_tool_stats_service

settings = get_settings()

class ToolClickRequest(BaseModel):
    tool_id: str

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

@app.get("/api/news", summary="资讯查询", tags=["天行数据"])
async def news(category: str = "internet"):
    """查询互联网资讯、电竞资讯、汽车新闻"""
    result = await TianApiService.get_info_news(category)
    return result

@app.get("/api/news/detail", summary="资讯详情", tags=["天行数据"])
async def news_detail(url: str):
    """抓取并缓存资讯正文，供小程序原生详情页展示。"""
    result = await NewsDetailService.fetch_detail(url)
    return result

@app.get("/api/gold-price", summary="黄金行情", tags=["天行数据"])
async def gold_price():
    """查询黄金行情"""
    result = await TianApiService.get_gold_price()
    return result

@app.get("/api/crude-oil", summary="原油价格", tags=["天行数据"])
async def crude_oil():
    """查询国际原油价格"""
    result = await TianApiService.get_crude_oil()
    return result

@app.get("/api/daily-brief", summary="每日简报", tags=["天行数据"])
async def daily_brief():
    """查询每日简报。"""
    result = await TianApiService.get_daily_brief()
    return result

@app.get("/api/hot-search", summary="热搜榜", tags=["天行数据"])
async def hot_search(platform: str = "weibo"):
    """查询微博热搜榜或百度热搜。"""
    result = await TianApiService.get_hot_search(platform)
    return result

@app.get("/api/hot-search/detail", summary="热搜详情", tags=["天行数据"])
async def hot_search_detail(platform: str = "weibo", keyword: str = "", hot: str = "", description: str = "", url: str = ""):
    """按热搜关键词聚合站内资讯，生成小程序原生详情内容。"""
    result = await TianApiService.get_hot_search_detail(platform, keyword, hot, description, url)
    return result

@app.get("/api/location/reverse", summary="逆地址解析", tags=["定位服务"])
async def reverse_location(latitude: float, longitude: float):
    """根据经纬度解析省、市、区，用于天气和油价定位。"""
    result = await LocationService.reverse_geocode(latitude, longitude)
    return result

# ==================== 本地工具 API ====================

@app.get("/api/tools/popular", summary="热门工具排行", tags=["工具统计"])
async def popular_tools(limit: int = 4):
    """按全站点击次数返回热门工具。"""
    result = get_tool_stats_service().get_popular(limit)
    return {"code": 200, "msg": "success", "data": result}

@app.post("/api/tools/click", summary="记录工具点击", tags=["工具统计"])
async def record_tool_click(payload: ToolClickRequest):
    """记录一次工具点击，用于实时刷新全站热门工具。"""
    result = get_tool_stats_service().record_click(payload.tool_id)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "未知工具"))
    return result

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
            "天行数据": ["/api/oil-price", "/api/weather", "/api/calendar", "/api/news", "/api/gold-price", "/api/crude-oil"],
            "定位服务": ["/api/location/reverse"],
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
