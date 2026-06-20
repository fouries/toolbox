from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from starlette.background import BackgroundTask
import asyncio
import re
import httpx

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
async def news_detail(url: str, image: str = ""):
    """抓取并缓存资讯正文，供小程序原生详情页展示。"""
    result = await NewsDetailService.fetch_detail(url, preferred_image=image)
    return result

@app.get("/api/news/image-proxy", summary="资讯图片代理", tags=["天行数据"])
async def news_image_proxy(url: str):
    """代理资讯原文图片，便于小程序通过本站 HTTPS 域名展示。"""
    result = await NewsDetailService.fetch_image(url)
    if result.get("code") != 200:
        raise HTTPException(status_code=400 if result.get("code") == 400 else 502, detail=result.get("msg", "图片读取失败"))
    content = result.get("content") or b""
    return Response(content=content, media_type=str(result.get("content_type") or "image/jpeg"), headers={"Cache-Control": "public, max-age=86400"})

@app.get("/api/news/local/{local_id}", summary="本地资讯详情", tags=["天行数据"])
async def local_news_detail(local_id: str):
    """读取已下载到服务器本地的资讯正文快照。"""
    result = NewsDetailService.read_local_detail(local_id)
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
async def hot_search(platform: str = "baidu"):
    """查询百度热搜榜/抖音热搜榜。微博热搜入口已下线，传入其他 platform 时自动返回百度热搜。"""
    result = await TianApiService.get_hot_search(platform)
    return result

@app.get("/api/hot-search/detail", summary="热搜详情", tags=["天行数据"])
async def hot_search_detail(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜完整详情：百度包含摘要/视频/图片，抖音使用榜单字段生成摘要。"""
    result = await TianApiService.get_hot_search_detail(platform, keyword, hot, description, url, raw)
    return result

@app.get("/api/hot-search/detail-basic", summary="热搜轻详情", tags=["天行数据"])
async def hot_search_detail_basic(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜轻详情：只返回首屏所需字段，视频/图片/相关资讯由完整详情异步补齐。"""
    result = await TianApiService.get_hot_search_detail_basic(platform, keyword, hot, description, url, raw)
    return result

@app.get("/api/hot-search/detail-media", summary="热搜富媒体详情", tags=["天行数据"])
async def hot_search_detail_media(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜富媒体详情。当前复用完整详情缓存，供前端异步补齐。"""
    result = await TianApiService.get_hot_search_detail(platform, keyword, hot, description, url, raw)
    return result

@app.get("/api/image-proxy", summary="图片代理", tags=["本地工具"])
async def image_proxy(url: str):
    """代理百度热搜图片，便于小程序通过本站 HTTPS 域名加载缩略图。"""
    parsed = urlparse(url)
    allowed_hosts = ("bdstatic.com", "bcebos.com", "baidu.com")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not any(parsed.netloc == host or parsed.netloc.endswith(f".{host}") for host in allowed_hosts):
        raise HTTPException(status_code=400, detail="Unsupported image host")
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    content_type = response.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL is not an image")
    return Response(content=response.content, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/video-proxy", summary="视频代理", tags=["本地工具"])
async def video_proxy(url: str, request: Request):
    """代理百度热搜视频，避免直连百度视频资源时被防盗链/CORS/小程序域名限制拦截。"""
    parsed = urlparse(url)
    allowed_hosts = ("bdstatic.com", "bcebos.com", "baidu.com")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not any(parsed.netloc == host or parsed.netloc.endswith(f".{host}") for host in allowed_hosts):
        raise HTTPException(status_code=400, detail="Unsupported video host")
    if not re.search(r"\.(?:mp4|m3u8)(?:\?|$)", url, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail="URL is not a supported video")

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "Referer": "https://m.baidu.com/",
        "Accept": "video/*,*/*;q=0.8",
    }
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=30, follow_redirects=True)
    try:
        upstream = await client.send(client.build_request("GET", url, headers=headers), stream=True)
        upstream.raise_for_status()
    except Exception as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"视频读取失败: {exc}")

    response_headers = {
        "Cache-Control": "public, max-age=3600",
        "Accept-Ranges": upstream.headers.get("accept-ranges", "bytes"),
    }
    for header_name in ("content-length", "content-range"):
        header_value = upstream.headers.get(header_name)
        if header_value:
            response_headers[header_name.title()] = header_value
    media_type = upstream.headers.get("content-type") or ("application/vnd.apple.mpegurl" if parsed.path.lower().endswith(".m3u8") else "video/mp4")
    return StreamingResponse(
        upstream.aiter_bytes(),
        status_code=upstream.status_code,
        media_type=media_type,
        headers=response_headers,
        background=BackgroundTask(client.aclose),
    )

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
