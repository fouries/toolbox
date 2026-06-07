import math
from typing import Any, Dict

from utils.cache import cache, make_cache_key
from utils.http_client import HttpClient

REVERSE_GEOCODE_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _pick_city(data: Dict[str, Any]) -> str:
    for key in ("city", "locality"):
        value = _clean_text(data.get(key))
        if value:
            return value

    for item in data.get("localityInfo", {}).get("administrative", []):
        name = _clean_text(item.get("name"))
        admin_level = item.get("adminLevel")
        if name and admin_level in (6, 7, 8):
            return name
    return ""


class LocationService:
    """定位相关服务。前端只请求本站 API，避免小程序额外配置第三方 request 域名。"""

    @staticmethod
    async def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]:
        if not (math.isfinite(latitude) and math.isfinite(longitude)):
            return {"code": 400, "msg": "经纬度参数不合法"}
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return {"code": 400, "msg": "经纬度参数不合法"}

        rounded_lat = round(latitude, 4)
        rounded_lng = round(longitude, 4)
        cache_key = make_cache_key("reverse_geocode", lat=rounded_lat, lng=rounded_lng)
        cached = await cache.get(cache_key)
        if cached:
            return {"code": 200, "msg": "success", "from_cache": True, "data": cached}

        async with HttpClient(timeout=10) as client:
            result = await client.get(
                REVERSE_GEOCODE_URL,
                params={
                    "latitude": rounded_lat,
                    "longitude": rounded_lng,
                    "localityLanguage": "zh",
                },
            )

        if result.get("error"):
            return {"code": 502, "msg": "逆地址解析失败，请稍后重试", "detail": result.get("error")}

        address = {
            "province": _clean_text(result.get("principalSubdivision")),
            "city": _pick_city(result),
            "district": _clean_text(result.get("locality")),
            "country": _clean_text(result.get("countryName")),
        }

        if not address["province"] and not address["city"]:
            return {"code": 404, "msg": "未能识别当前位置所在城市"}

        await cache.set(cache_key, address, 24 * 60 * 60)
        return {"code": 200, "msg": "success", "data": address}
