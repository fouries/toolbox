import json
import logging
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from urllib.parse import unquote, urlparse
from starlette.background import BackgroundTask
import asyncio
import re
import httpx

from config import get_settings
from core.logging import setup_logging
from core.middleware import RequestLoggingMiddleware
from core.responses import error, normalize_response, success
from db.session import init_db
from utils.cache import cache
from utils.url_security import is_allowed_host, is_public_http_url
from api.document_converter import get_document_converter_service
from api.image_tools import get_image_toolbox_service
from api.media_converter import get_media_converter_service
from api.tianapi import TianApiService
from api.news_detail import NewsDetailService
from api.tools import ToolsService
from api.location import LocationService
from api.tool_stats import get_tool_stats_service
from api.user_engagement import get_user_engagement_service
from api.wechat_subscribe import get_wechat_subscribe_service
from api.user_favorites import get_user_favorites_service
from services.content_service import ContentService

settings = get_settings()
setup_logging(settings.LOG_LEVEL, settings.LOG_DIR)
logger = logging.getLogger(__name__)


def _extract_proxy_target_from_query(url: str, raw_query: str) -> str:
    """Return the full proxied target URL, preserving its nested query string.

    Mini-program/H5 media components may request `/api/*-proxy?url=https://...?...&x=...`
    when a proxy URL was over-decoded on the client. FastAPI then binds only the
    part before the first `&` to `url`, so recover the complete value from the
    raw query string. Use `unquote` (not `unquote_plus`) because signed media
    URLs can contain literal `+` characters.
    """
    raw_query = str(raw_query or "")
    if raw_query.startswith("url="):
        raw_target = raw_query[len("url="):]
        if raw_target:
            try:
                return unquote(raw_target)
            except Exception:
                return raw_target
    return str(url or "")


def _extract_proxy_target_url(url: str, request: Request) -> str:
    return _extract_proxy_target_from_query(url, str(request.url.query or ""))


def _check_admin_key(x_admin_key: str = "") -> None:
    configured = str(getattr(settings, "ADMIN_KEY", "") or "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="后台管理密钥未配置")
    if not x_admin_key or x_admin_key != configured:
        raise HTTPException(status_code=401, detail="后台管理密钥无效")

class ToolClickRequest(BaseModel):
    tool_id: str


class UserIdentityRequest(BaseModel):
    user_key: str


class UserFavoriteRequest(BaseModel):
    user_key: str
    tool_id: str


class FeedbackRequest(BaseModel):
    user_key: str
    category: str = "idea"
    content: str
    contact: str = ""
    page: str = ""


class ReminderRequest(BaseModel):
    user_key: str
    reminder_type: str
    title: str = ""
    reminder_time: str
    enabled: bool = True
    wx_template_id: str = ""
    wx_subscribe_enabled: bool = False


class WechatLoginRequest(BaseModel):
    user_key: str
    code: str

class AdminFeedbackStatusRequest(BaseModel):
    status: str

class ImageToolboxBase64Request(BaseModel):
    filename: str
    content_base64: str
    operation: str
    options: dict = Field(default_factory=dict)


class DocumentConvertBase64Request(BaseModel):
    filename: str
    content_base64: str
    target_format: str


class DocumentOperationFile(BaseModel):
    filename: str
    content_base64: str


class PdfOperationBase64Request(BaseModel):
    operation: str
    files: list[DocumentOperationFile]
    pages: str = ""
    text: str = ""
    compression_level: str = "medium"


class DocumentScanBase64Request(BaseModel):
    files: list[DocumentOperationFile]
    target_format: str = "pdf"
    title: str = "扫描文档"
    mode: str = "color"


class MediaConvertBase64Request(BaseModel):
    operation: str
    files: list[DocumentOperationFile] = Field(default_factory=list)
    options: dict = Field(default_factory=dict)


class MediaUrlExtractRequest(BaseModel):
    url: str
    target_format: str = "mp3"

class MediaTaskInitRequest(BaseModel):
    operation: str
    options: dict = Field(default_factory=dict)


MEDIA_TASK_DIR = Path(__file__).resolve().parent / "data" / "media_tasks"
MEDIA_TASK_TTL = timedelta(hours=6)
MEDIA_TASK_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="media-converter")
MEDIA_TASKS: dict[str, dict[str, Any]] = {}


def _media_task_now() -> datetime:
    return datetime.utcnow()


def _cleanup_media_tasks() -> None:
    MEDIA_TASK_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = _media_task_now() - MEDIA_TASK_TTL
    stale_ids = [task_id for task_id, task in MEDIA_TASKS.items() if task.get("updated_at", task.get("created_at", cutoff)) < cutoff]
    for task_id in stale_ids:
        task_dir = MEDIA_TASK_DIR / task_id
        if task_dir.exists():
            shutil.rmtree(task_dir, ignore_errors=True)
        MEDIA_TASKS.pop(task_id, None)
    for task_dir in MEDIA_TASK_DIR.iterdir():
        if not task_dir.is_dir():
            continue
        try:
            if datetime.fromtimestamp(task_dir.stat().st_mtime) < cutoff:
                shutil.rmtree(task_dir, ignore_errors=True)
        except OSError:
            pass


def _serialize_media_task(task_id: str, task: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "task_id": task_id,
        "status": task.get("status", "pending"),
        "progress": int(task.get("progress", 0)),
        "message": task.get("message", ""),
        "operation": task.get("operation", ""),
    }
    if task.get("error"):
        data["error"] = task["error"]
    if task.get("text") is not None:
        data["text"] = task.get("text", "")
        data["language"] = task.get("language")
        data["duration"] = task.get("duration")
    if task.get("filename"):
        data["filename"] = task["filename"]
        data["media_type"] = task.get("media_type", "application/octet-stream")
        data["download_url"] = f"/api/media/tasks/{task_id}/download"
    return data


def _run_media_conversion_task(task_id: str) -> None:
    task = MEDIA_TASKS.get(task_id)
    if not task:
        return
    task["status"] = "running"
    task["progress"] = 20
    task["message"] = "正在处理音视频，请稍候..."
    task["updated_at"] = _media_task_now()
    try:
        service = get_media_converter_service()
        if task.get("url"):
            import asyncio as _asyncio
            result = _asyncio.run(service.extract_audio_from_url(str(task["url"]), str(task.get("target_format") or "mp3")))
        else:
            files = []
            for item in task.get("files", []):
                files.append({"filename": item["filename"], "content": Path(item["path"]).read_bytes()})
            task["progress"] = 45
            task["message"] = "文件已上传，正在转换..."
            task["updated_at"] = _media_task_now()
            result = service.process(str(task.get("operation") or ""), files, task.get("options") or {})
        if result.get("code") == 400:
            raise ValueError(str(result.get("msg") or "音视频处理失败"))
        data = result.get("data")
        if data is not None:
            task.update({
                "status": "completed",
                "progress": 100,
                "message": "识别完成",
                "text": str(data.get("text") or ""),
                "language": data.get("language"),
                "duration": data.get("duration"),
                "updated_at": _media_task_now(),
            })
            return
        output_path = Path(task["task_dir"]) / str(result["filename"])
        output_path.write_bytes(result["content"])
        task.update({
            "status": "completed",
            "progress": 100,
            "message": "处理完成，请下载结果文件",
            "filename": result["filename"],
            "media_type": result["media_type"],
            "output_path": str(output_path),
            "updated_at": _media_task_now(),
        })
    except Exception as exc:
        task.update({
            "status": "failed",
            "progress": 100,
            "message": "处理失败",
            "error": str(exc),
            "updated_at": _media_task_now(),
        })

async def _wechat_reminder_loop():
    while True:
        try:
            await get_wechat_subscribe_service().send_due_reminders()
        except Exception as exc:
            logger.warning("wechat_reminder_loop_failed error=%s", exc)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时：初始化数据库、迁移旧 JSON 点击统计、连接缓存
    init_db()
    _cleanup_media_tasks()
    get_tool_stats_service().migrate_legacy_json()
    await cache.init()
    reminder_task = asyncio.create_task(_wechat_reminder_loop())
    try:
        yield
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass
        # 关闭时：清理资源
        await cache.close()

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
app.add_middleware(RequestLoggingMiddleware)

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error(code=exc.status_code, msg=str(exc.detail or "请求失败")),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=error(code=500, msg="服务器内部错误")
    )

# ==================== 天行数据 API ====================

@app.get("/api/oil-price", summary="油价查询", tags=["天行数据"])
async def oil_price(province: str = "北京"):
    """查询各省份油价"""
    result = await TianApiService.get_oil_price(province)
    return normalize_response(result)

@app.get("/api/weather", summary="天气预报", tags=["天行数据"])
async def weather(city: str = "北京"):
    """查询城市天气"""
    result = await TianApiService.get_weather(city)
    return normalize_response(result)

@app.get("/api/calendar", summary="黄历日历", tags=["天行数据"])
async def calendar(date: str = None):
    """黄历/日历查询"""
    result = await TianApiService.get_calendar(date)
    return normalize_response(result)

@app.get("/api/news", summary="资讯查询", tags=["天行数据"])
async def news(category: str = "internet"):
    """查询互联网资讯、电竞资讯、汽车新闻"""
    result = await ContentService.get_info_news(category)
    return normalize_response(result)

@app.get("/api/news/detail", summary="资讯详情", tags=["天行数据"])
async def news_detail(url: str, image: str = ""):
    """抓取并缓存资讯正文，供小程序原生详情页展示。"""
    result = await NewsDetailService.fetch_detail(url, preferred_image=image)
    return normalize_response(result)

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
    return normalize_response(result)

@app.get("/api/gold-price", summary="黄金行情", tags=["天行数据"])
async def gold_price():
    """查询黄金行情"""
    result = await TianApiService.get_gold_price()
    return normalize_response(result)

@app.get("/api/crude-oil", summary="原油价格", tags=["天行数据"])
async def crude_oil():
    """查询国际原油价格"""
    result = await TianApiService.get_crude_oil()
    return normalize_response(result)

@app.get("/api/daily-brief", summary="每日简报", tags=["天行数据"])
async def daily_brief():
    """查询每日简报。"""
    result = await ContentService.get_daily_brief()
    return normalize_response(result)

@app.get("/api/hot-search", summary="热搜榜", tags=["天行数据"])
async def hot_search(platform: str = "baidu"):
    """查询百度热搜榜/抖音热搜榜。微博热搜入口已下线，传入其他 platform 时自动返回百度热搜。"""
    result = await ContentService.get_hot_search(platform)
    return normalize_response(result)

@app.get("/api/hot-search/detail", summary="热搜详情", tags=["天行数据"])
async def hot_search_detail(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜完整详情：百度包含摘要/视频/图片，抖音使用榜单字段生成摘要。"""
    result = await ContentService.get_hot_search_detail(platform, keyword, hot, description, url, raw)
    return normalize_response(result)

@app.get("/api/hot-search/detail-basic", summary="热搜轻详情", tags=["天行数据"])
async def hot_search_detail_basic(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜轻详情：只返回首屏所需字段，视频/图片/相关资讯由完整详情异步补齐。"""
    result = await TianApiService.get_hot_search_detail_basic(platform, keyword, hot, description, url, raw)
    return normalize_response(result)

@app.get("/api/hot-search/detail-media", summary="热搜富媒体详情", tags=["天行数据"])
async def hot_search_detail_media(platform: str = "baidu", keyword: str = "", hot: str = "", description: str = "", url: str = "", raw: str = ""):
    """生成热搜富媒体详情。当前复用完整详情缓存，供前端异步补齐。"""
    result = await ContentService.get_hot_search_detail(platform, keyword, hot, description, url, raw)
    return normalize_response(result)

@app.get("/api/image-proxy", summary="图片代理", tags=["本地工具"])
async def image_proxy(url: str, request: Request):
    """代理热搜图片，便于小程序通过本站 HTTPS 域名加载缩略图。"""
    url = _extract_proxy_target_url(url, request)
    parsed = urlparse(url)
    allowed_hosts = ("bdstatic.com", "bcebos.com", "baidu.com", "douyinpic.com", "byteimg.com")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not is_allowed_host(url, allowed_hosts) or not is_public_http_url(url):
        raise HTTPException(status_code=400, detail="Unsupported image host")
    is_douyin_image = any(parsed.netloc == host or parsed.netloc.endswith(f".{host}") for host in ("douyinpic.com", "byteimg.com"))
    referer = "https://www.douyin.com/" if is_douyin_image else "https://m.baidu.com/"
    async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
        try:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": referer, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"图片读取失败: {exc}")
    content_type = response.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL is not an image")
    return Response(content=response.content, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/video-proxy", summary="视频代理", tags=["本地工具"])
async def video_proxy(url: str, request: Request):
    """代理热搜视频，避免直连视频资源时被防盗链/CORS/小程序域名限制拦截。"""
    url = _extract_proxy_target_url(url, request)
    parsed = urlparse(url)
    allowed_hosts = ("bdstatic.com", "bcebos.com", "baidu.com", "douyinvod.com")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not is_allowed_host(url, allowed_hosts) or not is_public_http_url(url):
        raise HTTPException(status_code=400, detail="Unsupported video host")
    if not re.search(r"(?:\.(?:mp4|m3u8)(?:\?|$)|mime_type=video_)", url, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail="URL is not a supported video")

    is_douyin_video = parsed.netloc == "douyinvod.com" or parsed.netloc.endswith(".douyinvod.com")
    referer = "https://www.douyin.com/" if is_douyin_video else "https://m.baidu.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "Referer": referer,
        "Accept": "video/*,*/*;q=0.8",
    }
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=30, follow_redirects=False)
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
    return normalize_response(result)

# ==================== 本地工具 API ====================

@app.get("/api/tools/popular", summary="热门工具排行", tags=["工具统计"])
async def popular_tools(limit: int = 4):
    """按全站点击次数返回热门工具。"""
    result = get_tool_stats_service().get_popular(limit)
    return success(result)

@app.post("/api/tools/click", summary="记录工具点击", tags=["工具统计"])
async def record_tool_click(payload: ToolClickRequest):
    """记录一次工具点击，用于实时刷新全站热门工具。"""
    result = get_tool_stats_service().record_click(payload.tool_id)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "未知工具"))
    return normalize_response(result)

@app.post("/api/users/anonymous", summary="创建/刷新匿名用户", tags=["轻量用户"])
async def ensure_anonymous_user(payload: UserIdentityRequest):
    """第一阶段轻量身份：H5 本地生成 user_key，小程序后续可替换为 openid。"""
    result = get_user_favorites_service().ensure_user(payload.user_key)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "用户标识无效"))
    return normalize_response(result)

@app.get("/api/users/favorites", summary="获取工具收藏", tags=["轻量用户"])
async def list_user_favorites(user_key: str):
    result = get_user_favorites_service().list_favorites(user_key)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "用户标识无效"))
    return normalize_response(result)

@app.post("/api/users/favorites", summary="收藏工具", tags=["轻量用户"])
async def add_user_favorite(payload: UserFavoriteRequest):
    result = get_user_favorites_service().add_favorite(payload.user_key, payload.tool_id)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "收藏失败"))
    return normalize_response(result)

@app.delete("/api/users/favorites", summary="取消收藏工具", tags=["轻量用户"])
async def remove_user_favorite(payload: UserFavoriteRequest):
    result = get_user_favorites_service().remove_favorite(payload.user_key, payload.tool_id)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "取消收藏失败"))
    return normalize_response(result)

@app.post("/api/feedback", summary="提交反馈建议", tags=["反馈订阅"])
async def submit_feedback(payload: FeedbackRequest):
    result = get_user_engagement_service().submit_feedback(
        payload.user_key,
        payload.category,
        payload.content,
        payload.contact,
        payload.page,
    )
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "提交反馈失败"))
    return normalize_response(result)

@app.get("/api/feedback", summary="获取我的反馈", tags=["反馈订阅"])
async def list_feedback(user_key: str):
    result = get_user_engagement_service().list_feedback(user_key)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "用户标识无效"))
    return normalize_response(result)

@app.get("/api/admin/feedback", summary="后台反馈列表", tags=["反馈订阅"])
async def admin_list_feedback(status: str = "", category: str = "", limit: int = 100, x_admin_key: str = Header(default="")):
    _check_admin_key(x_admin_key)
    result = get_user_engagement_service().list_all_feedback(status, category, limit)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "查询反馈失败"))
    return normalize_response(result)

@app.patch("/api/admin/feedback/{feedback_id}", summary="更新反馈状态", tags=["反馈订阅"])
async def admin_update_feedback(feedback_id: int, payload: AdminFeedbackStatusRequest, x_admin_key: str = Header(default="")):
    _check_admin_key(x_admin_key)
    result = get_user_engagement_service().update_feedback_status(feedback_id, payload.status)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "更新反馈失败"))
    if result.get("code") == 404:
        raise HTTPException(status_code=404, detail=result.get("msg", "反馈不存在"))
    return normalize_response(result)

@app.get("/api/reminders", summary="获取订阅提醒", tags=["反馈订阅"])
async def list_reminders(user_key: str):
    result = get_user_engagement_service().list_reminders(user_key)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "用户标识无效"))
    return normalize_response(result)

@app.post("/api/reminders", summary="保存订阅提醒", tags=["反馈订阅"])
async def upsert_reminder(payload: ReminderRequest):
    configured_template = get_wechat_subscribe_service().template_id_for(payload.reminder_type)
    wx_template_id = configured_template
    wx_subscribe_enabled = bool(payload.enabled and configured_template and payload.wx_subscribe_enabled)
    result = get_user_engagement_service().upsert_reminder(
        payload.user_key,
        payload.reminder_type,
        payload.title,
        payload.reminder_time,
        payload.enabled,
        wx_template_id=wx_template_id,
        wx_subscribe_enabled=wx_subscribe_enabled,
    )
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "保存提醒失败"))
    return normalize_response(result)


@app.get("/api/wechat/subscribe-config", summary="获取微信订阅消息模板配置", tags=["反馈订阅"])
async def get_wechat_subscribe_config():
    templates = get_wechat_subscribe_service().configured_templates()
    return success({
        "enabled": bool(settings.WECHAT_SUBSCRIBE_ENABLED and settings.WECHAT_MINI_APP_ID),
        "templates": templates,
    })


@app.post("/api/wechat/login", summary="绑定微信小程序 openid", tags=["反馈订阅"])
async def bind_wechat_login(payload: WechatLoginRequest):
    result = await get_wechat_subscribe_service().bind_openid(payload.user_key, payload.code)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "微信登录失败"))
    if result.get("code") == 503:
        raise HTTPException(status_code=503, detail=result.get("msg", "微信配置缺失"))
    return normalize_response(result)


@app.delete("/api/reminders", summary="关闭订阅提醒", tags=["反馈订阅"])
async def disable_reminder(payload: ReminderRequest):
    result = get_user_engagement_service().disable_reminder(payload.user_key, payload.reminder_type)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "关闭提醒失败"))
    if result.get("code") == 404:
        raise HTTPException(status_code=404, detail=result.get("msg", "提醒不存在"))
    return normalize_response(result)

@app.get("/api/qrcode", summary="二维码生成", tags=["本地工具"])
async def generate_qrcode(text: str, size: int = 256):
    """生成二维码图片（base64格式）"""
    result = ToolsService.generate_qrcode(text, size)
    return normalize_response(result)

@app.get("/api/barcode", summary="条形码生成", tags=["本地工具"])
async def generate_barcode(text: str, height: int = 120):
    result = ToolsService.generate_barcode(text, height)
    return normalize_response(result)

@app.post("/api/images/process-base64", summary="图片工具箱处理（Base64）", tags=["本地工具"])
async def image_toolbox_process_base64(payload: ImageToolboxBase64Request):
    result = get_image_toolbox_service().process_base64(payload.filename, payload.content_base64, payload.operation, payload.options or {})
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "图片处理失败"))
    data = result.get("data")
    if data is not None:
        return success(data)
    import base64
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })

@app.post("/api/documents/convert", summary="文档格式转换", tags=["本地工具"])
async def convert_document(file: UploadFile = File(...), target_format: str = Form(...)):
    """常见文档格式互转：TXT、HTML、DOCX、PDF。转换结果直接下载，不长期保存。"""
    result = await get_document_converter_service().convert(file, target_format)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "文档转换失败"))
    return Response(
        content=result["content"],
        media_type=result["media_type"],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(str(result['filename']))}",
            "Cache-Control": "no-store",
        },
    )

@app.post("/api/documents/convert-base64", summary="文档格式转换（Base64）", tags=["本地工具"])
async def convert_document_base64(payload: DocumentConvertBase64Request):
    """小程序/H5 兼容接口：接收 base64 文件内容，返回 base64 转换结果。"""
    import base64

    try:
        raw = base64.b64decode(payload.content_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="文件内容不是有效的 Base64")
    upload = UploadFile(filename=payload.filename, file=BytesIO(raw))
    result = await get_document_converter_service().convert(upload, payload.target_format)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "文档转换失败"))
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })


@app.post("/api/documents/pdf-operation-base64", summary="PDF 合并/拆分/压缩/编辑/去水印（Base64）", tags=["本地工具"])
async def pdf_operation_base64(payload: PdfOperationBase64Request):
    """小程序/H5 兼容接口：PDF 合并、页面提取、压缩、添加文字、去水印。"""
    import base64

    decoded_files = []
    for item in payload.files:
        try:
            raw = base64.b64decode(item.content_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail=f"{item.filename} 不是有效的 Base64")
        decoded_files.append({"filename": item.filename, "content": raw})
    result = get_document_converter_service().operate_pdf(payload.operation, decoded_files, payload.pages, payload.text, payload.compression_level)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "PDF 处理失败"))
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })


@app.post("/api/documents/scan-base64", summary="扫描图片生成文档（Base64）", tags=["本地工具"])
async def document_scan_base64(payload: DocumentScanBase64Request):
    """小程序/H5 兼容接口：接收多张拍照/图片内容，生成 PDF、Word 或 PPT。"""
    import base64

    decoded_files = []
    for item in payload.files:
        try:
            raw = base64.b64decode(item.content_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail=f"{item.filename} 不是有效的 Base64")
        decoded_files.append({"filename": item.filename, "content": raw})
    result = get_document_converter_service().scan_images(decoded_files, payload.target_format, payload.title, payload.mode)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "扫描生成失败"))
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })


@app.post("/api/media/convert-base64", summary="音视频转换处理（Base64）", tags=["本地工具"])
async def media_convert_base64(payload: MediaConvertBase64Request):
    """小程序/H5 兼容接口：音频裁剪、拼接、合并、转文字、人声处理、音量调节、视频转音频。"""
    import base64

    decoded_files = []
    for item in payload.files:
        try:
            raw = base64.b64decode(item.content_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail=f"{item.filename} 不是有效的 Base64")
        decoded_files.append({"filename": item.filename, "content": raw})
    result = get_media_converter_service().process(payload.operation, decoded_files, payload.options or {})
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "音视频处理失败"))
    data = result.get("data")
    if data is not None:
        return success(data)
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })


@app.post("/api/media/tasks", summary="创建音视频转换任务", tags=["本地工具"])
async def media_create_task(
    operation: str = Form(...),
    options: str = Form("{}"),
    files: list[UploadFile] = File(default=[]),
):
    """上传原始文件并后台处理，避免大文件 Base64 往返。"""
    _cleanup_media_tasks()
    operation = str(operation or "").strip().lower()
    try:
        parsed_options = json.loads(options or "{}")
        if not isinstance(parsed_options, dict):
            parsed_options = {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="options 不是有效 JSON")
    task_id = uuid.uuid4().hex
    task_dir = MEDIA_TASK_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for idx, upload in enumerate(files or []):
        safe_name = Path(upload.filename or f"media-{idx}").name or f"media-{idx}"
        input_path = task_dir / f"input_{idx}_{safe_name}"
        size = 0
        with input_path.open("wb") as fh:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > 50 * 1024 * 1024:
                    shutil.rmtree(task_dir, ignore_errors=True)
                    raise HTTPException(status_code=400, detail=f"{safe_name} 超过 50MB 限制")
                fh.write(chunk)
        saved_files.append({"filename": safe_name, "path": str(input_path), "size": size})
    task = {
        "operation": operation,
        "options": parsed_options,
        "files": saved_files,
        "task_dir": str(task_dir),
        "status": "pending",
        "progress": 5,
        "message": "任务已创建，等待处理...",
        "created_at": _media_task_now(),
        "updated_at": _media_task_now(),
    }
    MEDIA_TASKS[task_id] = task
    MEDIA_TASK_EXECUTOR.submit(_run_media_conversion_task, task_id)
    return success(_serialize_media_task(task_id, task))


@app.post("/api/media/url-tasks", summary="创建视频链接提取音频任务", tags=["本地工具"])
async def media_create_url_task(payload: MediaUrlExtractRequest):
    """后台下载直链视频/音频并提取音频。"""
    _cleanup_media_tasks()
    parsed = urlparse(str(payload.url or "").strip())
    if parsed.scheme not in {"http", "https"} or not is_public_http_url(str(payload.url or "")):
        raise HTTPException(status_code=400, detail="仅支持公网 http/https 视频直链")
    task_id = uuid.uuid4().hex
    task_dir = MEDIA_TASK_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task = {
        "operation": "url_extract",
        "url": str(payload.url).strip(),
        "target_format": payload.target_format,
        "task_dir": str(task_dir),
        "status": "pending",
        "progress": 5,
        "message": "链接任务已创建，等待下载...",
        "created_at": _media_task_now(),
        "updated_at": _media_task_now(),
    }
    MEDIA_TASKS[task_id] = task
    MEDIA_TASK_EXECUTOR.submit(_run_media_conversion_task, task_id)
    return success(_serialize_media_task(task_id, task))


@app.get("/api/media/tasks/{task_id}", summary="查询音视频转换任务", tags=["本地工具"])
async def media_get_task(task_id: str):
    task = MEDIA_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return success(_serialize_media_task(task_id, task))


@app.post("/api/media/tasks/init", summary="初始化音视频转换任务", tags=["本地工具"])
async def media_init_task(payload: MediaTaskInitRequest):
    """初始化任务，供小程序多文件逐个上传后再启动。"""
    _cleanup_media_tasks()
    task_id = uuid.uuid4().hex
    task_dir = MEDIA_TASK_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task = {
        "operation": str(payload.operation or "").strip().lower(),
        "options": payload.options or {},
        "files": [],
        "task_dir": str(task_dir),
        "status": "pending",
        "progress": 5,
        "message": "任务已创建，请上传文件...",
        "created_at": _media_task_now(),
        "updated_at": _media_task_now(),
    }
    MEDIA_TASKS[task_id] = task
    return success(_serialize_media_task(task_id, task))


@app.post("/api/media/tasks/{task_id}/files", summary="上传音视频任务文件", tags=["本地工具"])
async def media_upload_task_file(task_id: str, file: UploadFile = File(...)):
    task = MEDIA_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.get("status") not in {"pending", "failed"}:
        raise HTTPException(status_code=400, detail="任务已启动，不能继续上传文件")
    task_dir = Path(str(task["task_dir"]))
    task_dir.mkdir(parents=True, exist_ok=True)
    files_list = task.setdefault("files", [])
    safe_name = Path(file.filename or f"media-{len(files_list)}").name or f"media-{len(files_list)}"
    input_path = task_dir / f"input_{len(files_list)}_{safe_name}"
    size = 0
    with input_path.open("wb") as fh:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > 50 * 1024 * 1024:
                input_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail=f"{safe_name} 超过 50MB 限制")
            fh.write(chunk)
    files_list.append({"filename": safe_name, "path": str(input_path), "size": size})
    task.update({"progress": min(30, 5 + len(files_list) * 5), "message": f"已上传 {len(files_list)} 个文件", "updated_at": _media_task_now()})
    return success(_serialize_media_task(task_id, task))


@app.post("/api/media/tasks/{task_id}/start", summary="启动音视频转换任务", tags=["本地工具"])
async def media_start_task(task_id: str):
    task = MEDIA_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.get("status") == "running":
        return success(_serialize_media_task(task_id, task))
    task.update({"status": "pending", "progress": max(10, int(task.get("progress", 5))), "message": "任务已提交，等待处理...", "updated_at": _media_task_now()})
    MEDIA_TASK_EXECUTOR.submit(_run_media_conversion_task, task_id)
    return success(_serialize_media_task(task_id, task))


@app.get("/api/media/tasks/{task_id}/download", summary="下载音视频转换结果", tags=["本地工具"])
async def media_download_task(task_id: str):
    task = MEDIA_TASKS.get(task_id)
    if not task or task.get("status") != "completed" or not task.get("output_path"):
        raise HTTPException(status_code=404, detail="结果文件不存在或任务尚未完成")
    output_path = Path(str(task["output_path"]))
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="结果文件已过期")
    return FileResponse(
        output_path,
        media_type=str(task.get("media_type") or "application/octet-stream"),
        filename=str(task.get("filename") or output_path.name),
        headers={
            "Cache-Control": "private, max-age=21600",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
        },
    )


@app.post("/api/media/extract-url-audio", summary="视频链接提取音频（Base64）", tags=["本地工具"])
async def media_extract_url_audio(payload: MediaUrlExtractRequest):
    """从可直接下载的视频/音频链接中提取音频。"""
    import base64

    result = await get_media_converter_service().extract_audio_from_url(payload.url, payload.target_format)
    if result.get("code") == 400:
        raise HTTPException(status_code=400, detail=result.get("msg", "链接音频提取失败"))
    return success({
        "filename": result["filename"],
        "media_type": result["media_type"],
        "base64": base64.b64encode(result["content"]).decode("ascii"),
    })

@app.get("/api/password", summary="随机密码", tags=["本地工具"])
async def generate_password(length: int = 16, 
                           upper: bool = True,
                           lower: bool = True,
                           number: bool = True,
                           symbol: bool = True):
    """生成随机密码"""
    result = ToolsService.generate_password(length, upper, lower, number, symbol)
    return normalize_response(result)

@app.get("/api/base64/encode", summary="Base64编码", tags=["编码工具"])
async def base64_encode(text: str):
    """Base64编码"""
    result = ToolsService.base64_encode(text)
    return normalize_response(result)

@app.get("/api/base64/decode", summary="Base64解码", tags=["编码工具"])
async def base64_decode(encoded: str):
    """Base64解码"""
    result = ToolsService.base64_decode(encoded)
    return normalize_response(result)

@app.get("/api/url/encode", summary="URL编码", tags=["编码工具"])
async def url_encode(text: str):
    """URL编码"""
    result = ToolsService.url_encode(text)
    return normalize_response(result)

@app.get("/api/url/decode", summary="URL解码", tags=["编码工具"])
async def url_decode(encoded: str):
    """URL解码"""
    result = ToolsService.url_decode(encoded)
    return normalize_response(result)

@app.post("/api/json/format", summary="JSON格式化", tags=["编码工具"])
async def json_format(json_str: str, indent: int = 2):
    """JSON格式化"""
    result = ToolsService.json_format(json_str, indent)
    return normalize_response(result)

# ==================== 通用接口 ====================

@app.get("/", summary="API首页")
async def root():
    return success({
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
    })

@app.get("/health", summary="健康检查")
async def health():
    return success({"status": "ok", "redis": cache.enabled})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
