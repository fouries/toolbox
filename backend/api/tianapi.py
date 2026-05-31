from typing import Dict, Any, Optional
from utils.http_client import HttpClient
from utils.cache import cache, make_cache_key
from config import get_settings

settings = get_settings()

TIANAPI_BASE = "https://apis.tianapi.com"

class TianApiService:
    """天行数据API聚合服务"""
    
    @staticmethod
    def _get_params(key: str, **kwargs) -> Dict[str, str]:
        """构建请求参数"""
        params = {"key": key}
        params.update(kwargs)
        return {k: str(v) for k, v in params.items() if v is not None}
    
    @staticmethod
    async def _request(path: str, cache_key: str = None, cache_ttl: int = 300, **kwargs) -> Dict[str, Any]:
        """通用请求方法"""
        api_key = settings.TIANAPI_KEY
        
        if not api_key:
            # 返回模拟数据用于测试
            return {"code": 200, "msg": "success", "newslist": [{"note": "请在 .env 文件中配置 TIANAPI_KEY"}]}
        
        async with HttpClient() as client:
            params = TianApiService._get_params(api_key, **kwargs)
            
            # 尝试从缓存获取
            if cache_key:
                cached = await cache.get(cache_key)
                if cached:
                    return {"code": 200, "msg": "success", "from_cache": True, "newslist": cached}
            
            # 调用API
            url = f"{TIANAPI_BASE}{path}"
            result = await client.get(url, params=params)
            
            # 适配不同的返回格式
            if result.get("code") == 200 and "result" in result:
                result_data = result["result"]
                
                # 天气API特殊格式: result.list 是数组
                if isinstance(result_data, dict) and "list" in result_data and isinstance(result_data["list"], list):
                    # 天气API: 把城市信息加到每条数据里
                    for item in result_data["list"]:
                        item["area"] = result_data.get("area", kwargs.get("city", ""))
                        item["province"] = result_data.get("province", "")
                        item["areaid"] = result_data.get("areaid", "")
                        # 空气质量字段（天气API没有单独返回）
                        item["aqi"] = ""
                        item["quality"] = "未知"
                    result["newslist"] = result_data["list"]
                
                # 普通格式: result是数组
                elif isinstance(result_data, list):
                    result["newslist"] = result_data
                
                # 普通格式: result是单个对象
                else:
                    result["newslist"] = [result_data]
            
            # 缓存成功的结果
            if result.get("code") == 200 and cache_key and "newslist" in result:
                await cache.set(cache_key, result["newslist"], cache_ttl)
            
            return result
    
    @staticmethod
    async def get_oil_price(province: str = "北京") -> Dict[str, Any]:
        """油价查询
        province: 省份名称（北京、上海、广东等）
        """
        cache_key = make_cache_key("oil", prov=province)
        return await TianApiService._request(
            "/oilprice/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_OIL,
            prov=province  # 注意: 新API用 prov 而不是 province
        )
    
    @staticmethod
    async def get_weather(city: str = "北京") -> Dict[str, Any]:
        """天气预报
        city: 城市名称（北京、上海、广州等）
        """
        cache_key = make_cache_key("weather", city=city)
        return await TianApiService._request(
            "/tianqi/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_WEATHER,
            city=city
        )
    
    @staticmethod
    async def get_express(no: str, type: str = "auto") -> Dict[str, Any]:
        """快递查询
        no: 快递单号
        type: 快递公司代码（auto=自动识别）
        """
        cache_key = make_cache_key("express", no=no)
        return await TianApiService._request(
            "/kd/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_DEFAULT,
            number=no,
            type=type
        )
    
    @staticmethod
    async def get_phone_location(phone: str) -> Dict[str, Any]:
        """手机号归属地
        phone: 手机号（前7位或完整号码）
        """
        cache_key = make_cache_key("phone", phone=phone[:7])  # 只缓存前7位
        return await TianApiService._request(
            "/shouji/index",
            cache_key=cache_key,
            cache_ttl=86400 * 30,  # 手机号归属地缓存30天
            phone=phone[:7]
        )
    
    @staticmethod
    async def get_idcard_info(idcard: str) -> Dict[str, Any]:
        """身份证信息查询
        idcard: 身份证号
        """
        cache_key = make_cache_key("idcard", idcard=idcard[:6])  # 只缓存前6位地区码
        return await TianApiService._request(
            "/idcard/index",
            cache_key=cache_key,
            cache_ttl=86400 * 30,
            idcard=idcard
        )
    
    @staticmethod
    async def get_exchange_rate(from_currency: str = "USD", to_currency: str = "CNY") -> Dict[str, Any]:
        """汇率查询"""
        cache_key = make_cache_key("exchange", from_=from_currency, to_=to_currency)
        return await TianApiService._request(
            "/rate/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_DEFAULT,
            bank=0,  # 央行中间价
            money=from_currency,
            to_currency=to_currency
        )
    
    @staticmethod
    async def get_calendar(date: str = None) -> Dict[str, Any]:
        """黄历/日历查询"""
        params = {}
        if date:
            params["date"] = date
        
        cache_key = make_cache_key("calendar", date=date or "today")
        return await TianApiService._request(
            "/lunar/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_DEFAULT,
            **params
        )
