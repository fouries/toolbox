import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import quote
from utils.http_client import HttpClient
from utils.cache import cache, make_cache_key
from config import get_settings

settings = get_settings()

TIANAPI_BASE = "https://apis.tianapi.com"
BAIDU_TOP_API = "https://top.baidu.com/api/board"

class TianApiService:
    """天行数据API聚合服务"""

    GOLD_KIND_NAMES = {
        "au9999": "Au99.99 黄金",
        "au9995": "Au99.95 黄金",
        "agTplusD": "白银 T+D",
        "auTplusD": "黄金 T+D",
        "mAuTplusD": "迷你黄金 T+D",
    }

    @staticmethod
    def _fallback_news(category: str) -> List[Dict[str, str]]:
        mapping = {
            "internet": [
                {"title": "AI 应用加速落地，互联网产品进入智能化升级阶段", "description": "从搜索、办公到电商，智能助手正在成为互联网产品的新入口。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
                {"title": "云服务和大模型基础设施持续扩容", "description": "算力、数据和应用生态成为科技企业竞争重点。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
            ],
            "esports": [
                {"title": "电竞赛事热度提升，俱乐部商业化持续探索", "description": "主场、直播内容和品牌合作成为电竞生态的重要增长点。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
                {"title": "游戏版本更新带动战术变化", "description": "职业队伍围绕新版本持续调整阵容与打法。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
            ],
            "auto": [
                {"title": "新能源汽车市场竞争加剧，智能座舱成为亮点", "description": "车企持续围绕续航、补能和智能驾驶体验升级。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
                {"title": "用车成本与油电价格成为消费者关注重点", "description": "购车决策更重视全生命周期成本和补能便利性。", "source": "小巧的工具箱", "url": "https://quan1234.com/"},
            ],
        }
        now = datetime.now().strftime("%Y-%m-%d")
        return [{**item, "ctime": now} for item in mapping.get(category, mapping["internet"])]

    @staticmethod
    def _fallback_gold() -> List[Dict[str, str]]:
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            {"name": "国内黄金", "price": "--", "unit": "元/克", "updown": "--", "time": now},
            {"name": "国际现货黄金", "price": "--", "unit": "美元/盎司", "updown": "--", "time": now},
            {"name": "足金零售参考", "price": "--", "unit": "元/克", "updown": "--", "time": now},
        ]

    @staticmethod
    def _fallback_crude_oil() -> List[Dict[str, str]]:
        now = datetime.now().strftime("%Y-%m-%d")
        return [
            {"name": "WTI 原油", "price": "--", "unit": "美元/桶", "updown": "--", "time": now},
            {"name": "Brent 布伦特原油", "price": "--", "unit": "美元/桶", "updown": "--", "time": now},
        ]

    @staticmethod
    def _fallback_daily_brief() -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        titles = [
            "关注今日国内外重要新闻与民生动态",
            "留意天气、交通和出行服务信息",
            "市场行情波动频繁，投资消费请以权威信息为准",
            "热点内容实时变化，可稍后刷新获取最新简报",
        ]
        return {
            "date": today,
            "source": "小巧的工具箱",
            "items": [{"rank": index + 1, "title": title} for index, title in enumerate(titles)],
        }

    @staticmethod
    def _hot_search_title(platform: str) -> str:
        return "微博热搜榜" if platform == "weibo" else "百度热搜榜"

    @staticmethod
    def _empty_hot_search(platform: str) -> Dict[str, Any]:
        return {
            "platform": platform,
            "title": TianApiService._hot_search_title(platform),
            "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": [],
        }

    @staticmethod
    def _format_change(value: Any, rate: Any) -> str:
        if value in (None, "") and rate in (None, ""):
            return ""
        if value in (None, ""):
            return str(rate)
        if rate in (None, ""):
            return str(value)
        rate_text = str(rate)
        if rate_text and not rate_text.endswith("%"):
            rate_text = f"{rate_text}%"
        return f"{value} ({rate_text})"

    @staticmethod
    def _normalize_gold_item(item: Dict[str, Any]) -> Dict[str, str]:
        code = str(item.get("code") or "").strip()
        return {
            "name": TianApiService.GOLD_KIND_NAMES.get(code, code or "黄金"),
            "type": code,
            "price": str(item.get("latestprice") or item.get("price") or "--"),
            "unit": "元/克",
            "updown": TianApiService._format_change(item.get("rafvalue"), item.get("raf")),
            "time": str(item.get("updatetime") or item.get("time") or ""),
            "buypri": str(item.get("buyprice") or ""),
            "sellpri": str(item.get("sellprice") or ""),
        }

    @staticmethod
    def _normalize_crude_item(item: Dict[str, Any]) -> Dict[str, str]:
        return {
            "name": str(item.get("name") or "原油"),
            "type": str(item.get("code") or ""),
            "price": str(item.get("nowprice") or item.get("price") or "--"),
            "unit": "美元/桶",
            "updown": TianApiService._format_change(item.get("diffnum"), item.get("diffrate")),
            "time": str(item.get("updatetime") or item.get("time") or ""),
        }

    @staticmethod
    def _normalize_brief_line(value: Any, rank: int) -> Dict[str, Any]:
        if isinstance(value, dict):
            title = str(value.get("title") or value.get("content") or value.get("digest") or value.get("news") or "")
            url = str(value.get("url") or value.get("link") or "")
            source = str(value.get("source") or "")
        else:
            title = str(value or "")
            url = ""
            source = ""
        title = re.sub(r"^\s*\d+\s*[、.．-]\s*", "", title).strip()
        item: Dict[str, Any] = {"rank": rank, "title": title}
        if url:
            item["url"] = url
        if source:
            item["source"] = source
        return item

    @staticmethod
    def _normalize_daily_brief_result(result: Dict[str, Any]) -> Dict[str, Any]:
        raw = result.get("result") if isinstance(result.get("result"), dict) else result
        raw_items = raw.get("list") or raw.get("newslist") or raw.get("items") or []
        if isinstance(raw_items, str):
            raw_items = [line for line in re.split(r"[\n\r]+", raw_items) if line.strip()]
        items = [TianApiService._normalize_brief_line(item, index + 1) for index, item in enumerate(raw_items)]
        items = [item for item in items if item["title"]]
        return {
            "date": str(raw.get("ctime") or raw.get("date") or raw.get("time") or datetime.now().strftime("%Y-%m-%d")),
            "source": str(raw.get("source") or "每日简报"),
            "items": items,
        }

    @staticmethod
    def _normalize_hot_item(item: Dict[str, Any], rank: int, platform: str) -> Dict[str, Any]:
        title = str(item.get("hotword") or item.get("word") or item.get("note") or item.get("title") or item.get("keyword") or "")
        hot = str(item.get("hotwordnum") or item.get("hotScore") or item.get("num") or item.get("hot") or "")
        description = str(item.get("desc") or item.get("description") or "")
        url = str(item.get("url") or item.get("mobilUrl") or "")
        if not url and platform == "weibo" and title:
            word = str(item.get("word_scheme") or title)
            url = f"https://s.weibo.com/weibo?q={quote(word)}&t=31&band_rank=12&Refer=top"
        if not url and platform == "baidu" and title:
            url = f"https://m.baidu.com/s?word={quote(title)}&sa=fyb_news"
        return {
            "rank": rank,
            "title": title,
            "hot": hot,
            "description": description,
            "url": url,
            "raw": dict(item),
        }

    @staticmethod
    def _normalize_hot_search_result(platform: str, result: Dict[str, Any]) -> Dict[str, Any]:
        raw = result.get("result") if isinstance(result.get("result"), dict) else result
        raw_items = raw.get("list") or raw.get("newslist") or raw.get("data") or []
        items = []
        for index, item in enumerate(raw_items):
            if isinstance(item, dict):
                normalized = TianApiService._normalize_hot_item(item, index + 1, platform)
                if normalized["title"]:
                    items.append(normalized)
        return {
            "platform": platform,
            "title": TianApiService._hot_search_title(platform),
            "updateTime": str(raw.get("update_time") or raw.get("updatetime") or raw.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M")),
            "items": items,
        }
    
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
        fallback = kwargs.pop("fallback", None)
        
        if not api_key:
            # 返回模拟数据用于测试
            return {"code": 200, "msg": "success", "fallback": True, "newslist": fallback or [{"note": "请在 .env 文件中配置 TIANAPI_KEY"}]}
        
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

            if result.get("code") != 200 and fallback is not None:
                return {
                    "code": 200,
                    "msg": result.get("msg") or "success",
                    "fallback": True,
                    "upstream_code": result.get("code"),
                    "newslist": fallback,
                }
            
            # 适配不同的返回格式
            if result.get("code") == 200 and "result" in result:
                result_data = result["result"]
                
                # 天气API特殊格式: result.list 是数组，同时需要城市字段
                if path == "/tianqi/index" and isinstance(result_data, dict) and "list" in result_data and isinstance(result_data["list"], list):
                    # 天气API: 把城市信息加到每条数据里
                    for item in result_data["list"]:
                        item["area"] = result_data.get("area", kwargs.get("city", ""))
                        item["province"] = result_data.get("province", "")
                        item["areaid"] = result_data.get("areaid", "")
                        # 空气质量字段（天气API没有单独返回）
                        item["aqi"] = ""
                        item["quality"] = "未知"
                    result["newslist"] = result_data["list"]

                # 新版新闻/行情 API 常见格式: result.list 或 result.newslist
                elif isinstance(result_data, dict) and isinstance(result_data.get("list"), list):
                    result["newslist"] = result_data["list"]

                elif isinstance(result_data, dict) and isinstance(result_data.get("newslist"), list):
                    result["newslist"] = result_data["newslist"]
                
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

    @staticmethod
    async def get_info_news(category: str = "internet") -> Dict[str, Any]:
        """资讯查询：互联网、电竞、汽车新闻。"""
        endpoint_map = {
            "internet": "/internet/index",
            "esports": "/esports/index",
            "auto": "/auto/index",
        }
        category = category if category in endpoint_map else "internet"
        cache_key = make_cache_key("news", category=category)
        return await TianApiService._request(
            endpoint_map[category],
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_DEFAULT,
            num=10,
            form=1,
            fallback=TianApiService._fallback_news(category)
        )

    @staticmethod
    def _score_related_news(keyword: str, item: Dict[str, Any]) -> int:
        text = f"{item.get('title') or ''} {item.get('description') or ''} {item.get('source') or ''}".lower()
        keyword_text = keyword.lower().strip()
        if not keyword_text:
            return 0
        score = 0
        if keyword_text in text:
            score += 10
        for token in re.split(r"[\s,，。；;：:、#]+", keyword_text):
            token = token.strip()
            if token and token in text:
                score += 2
        return score

    @staticmethod
    def _normalize_related_news(item: Dict[str, Any]) -> Dict[str, str]:
        return {
            "title": str(item.get("title") or ""),
            "description": str(item.get("description") or item.get("digest") or ""),
            "source": str(item.get("source") or item.get("from") or ""),
            "ctime": str(item.get("ctime") or item.get("time") or ""),
            "url": str(item.get("url") or item.get("link") or ""),
            "picUrl": str(item.get("picUrl") or item.get("picurl") or ""),
        }

    @staticmethod
    def _clean_hot_description(description: str) -> str:
        description = str(description or "").strip()
        unavailable_markers = ("热搜接口暂不可用", "接口暂不可用", "展示备用热点分类")
        if not description or any(marker in description for marker in unavailable_markers):
            return ""
        return description

    @staticmethod
    def _fallback_hot_detail_description(platform_name: str, keyword: str) -> str:
        return f"“{keyword}”正在{platform_name}受到关注，相关讨论可能涉及新闻进展、公众反馈和后续影响。"

    @staticmethod
    def _parse_hot_raw(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if not raw:
            return {}
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @staticmethod
    def _build_hot_raw_section(platform_name: str, keyword: str, hot: str, desc_text: str, raw_item: Dict[str, Any]) -> Dict[str, str]:
        title = str(raw_item.get("word") or raw_item.get("hotword") or raw_item.get("title") or raw_item.get("keyword") or keyword)
        heat = str(raw_item.get("hotScore") or raw_item.get("hotwordnum") or raw_item.get("num") or raw_item.get("hot") or hot or "--")
        desc = TianApiService._clean_hot_description(str(raw_item.get("desc") or raw_item.get("description") or "")) or desc_text
        parts = [f"平台：{platform_name}", f"关键词：{title}"]
        if heat:
            parts.append(f"热度：{heat}")
        if desc:
            parts.append(f"接口摘要：{desc}")
        return {"title": f"{platform_name}返回信息", "body": "\n".join(parts)}

    @staticmethod
    def _build_hot_search_detail(
        platform: str,
        keyword: str,
        hot: str = "",
        description: str = "",
        url: str = "",
        related_news: Optional[List[Dict[str, Any]]] = None,
        raw_item: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        platform = platform if platform in {"weibo", "baidu"} else "weibo"
        platform_name = TianApiService._hot_search_title(platform)
        related_news = related_news or []
        title = f"{keyword} - 热搜详情" if keyword else "热搜详情"
        hot_text = f"，当前热度为 {hot}" if hot else ""
        desc_text = TianApiService._clean_hot_description(description) or TianApiService._fallback_hot_detail_description(platform_name, keyword)
        raw_item = raw_item or {}
        raw_section = TianApiService._build_hot_raw_section(platform_name, keyword, hot, desc_text, raw_item)
        news_content_lines = []
        for item in related_news[:5]:
            item_title = str(item.get("title") or "").strip()
            item_desc = str(item.get("description") or "").strip()
            if item_title and item_desc:
                news_content_lines.append(f"{item_title}：{item_desc}")
            elif item_title:
                news_content_lines.append(item_title)
            elif item_desc:
                news_content_lines.append(item_desc)
        news_content = "\n".join(news_content_lines)
        if news_content_lines:
            summary = news_content_lines[0]
            sections = [{"title": "相关新闻内容", "body": news_content}]
        else:
            summary = f"{keyword} 正在{platform_name}受到关注{hot_text}。{desc_text}" if keyword else desc_text
            sections = [raw_section]
        content = "\n".join(section["body"] for section in sections if section["body"])
        return {
            "platform": platform,
            "keyword": keyword,
            "title": title,
            "hot": hot,
            "description": description,
            "sourceUrl": url,
            "summary": summary,
            "content": content,
            "sections": sections,
            "relatedNews": related_news,
            "rawHotItem": raw_item,
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    @staticmethod
    async def get_hot_search_detail(
        platform: str = "weibo",
        keyword: str = "",
        hot: str = "",
        description: str = "",
        url: str = "",
        raw: str = "",
    ) -> Dict[str, Any]:
        """热搜详情：按热搜词聚合站内资讯并生成小程序可展示正文。"""
        keyword = str(keyword or "").strip()
        platform = platform if platform in {"weibo", "baidu"} else "weibo"
        all_news: List[Dict[str, Any]] = []
        for category in ("internet", "esports", "auto"):
            result = await TianApiService.get_info_news(category)
            if result.get("code") == 200 and isinstance(result.get("newslist"), list):
                all_news.extend(item for item in result["newslist"] if isinstance(item, dict))

        scored = []
        for item in all_news:
            normalized = TianApiService._normalize_related_news(item)
            if not normalized["title"]:
                continue
            scored.append((TianApiService._score_related_news(keyword, normalized), normalized))

        matched = [item for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True) if score > 0]
        if not matched:
            matched = [item for _score, item in scored[:8]]
        data = TianApiService._build_hot_search_detail(
            platform=platform,
            keyword=keyword,
            hot=str(hot or ""),
            description=str(description or ""),
            url=str(url or ""),
            related_news=matched[:8],
            raw_item=TianApiService._parse_hot_raw(raw),
        )
        return {"code": 200, "msg": "success", "data": data}

    @staticmethod
    async def get_gold_price() -> Dict[str, Any]:
        """黄金行情查询。"""
        cache_key = make_cache_key("gold", kinds="au9999,au9995,agTplusD")
        result = await TianApiService._request(
            "/gold/index",
            cache_key=cache_key,
            cache_ttl=settings.CACHE_TTL_DEFAULT,
            kinds="au9999,au9995,agTplusD",
            fallback=TianApiService._fallback_gold()
        )
        if result.get("code") == 200 and not result.get("fallback") and isinstance(result.get("newslist"), list):
            result["newslist"] = [TianApiService._normalize_gold_item(item) for item in result["newslist"]]
        return result

    @staticmethod
    async def get_crude_oil() -> Dict[str, Any]:
        """国际原油价格查询。"""
        if not settings.TIANAPI_KEY:
            return {"code": 200, "msg": "success", "newslist": TianApiService._fallback_crude_oil()}

        items: List[Dict[str, str]] = []
        upstream_errors: List[str] = []
        for crude_code in ("wti", "blt"):
            result = await TianApiService._request(
                "/crude/index",
                cache_key=make_cache_key("crude_oil", code=crude_code),
                cache_ttl=settings.CACHE_TTL_DEFAULT,
                code=crude_code
            )
            if result.get("code") == 200 and isinstance(result.get("newslist"), list) and result["newslist"]:
                item = result["newslist"][0]
                if isinstance(item, dict):
                    item.setdefault("code", crude_code)
                    items.append(TianApiService._normalize_crude_item(item))
            else:
                upstream_errors.append(str(result.get("msg") or result.get("error") or crude_code))

        if items:
            return {"code": 200, "msg": "success", "newslist": items}

        return {
            "code": 200,
            "msg": "; ".join(upstream_errors) or "原油接口暂不可用",
            "fallback": True,
            "newslist": TianApiService._fallback_crude_oil()
        }

    @staticmethod
    async def get_daily_brief() -> Dict[str, Any]:
        """每日简报。"""
        if not settings.TIANAPI_KEY:
            return {"code": 200, "msg": "success", "fallback": True, "data": TianApiService._fallback_daily_brief()}
        result = await TianApiService._request(
            "/bulletin/index",
            cache_key=make_cache_key("daily_brief", date=datetime.now().strftime("%Y-%m-%d")),
            cache_ttl=settings.CACHE_TTL_DEFAULT,
        )
        if result.get("code") == 200:
            data = TianApiService._normalize_daily_brief_result(result)
            if data["items"]:
                return {"code": 200, "msg": "success", "data": data}
        return {"code": 200, "msg": result.get("msg") or "每日简报接口暂不可用", "fallback": True, "data": TianApiService._fallback_daily_brief()}

    @staticmethod
    def _proxied_baidu_image_url(image_url: str) -> str:
        image_url = str(image_url or "").strip()
        if not image_url:
            return ""
        return f"https://quan1234.com/api/image-proxy?url={quote(image_url, safe='')}"

    @staticmethod
    def _normalize_baidu_top_api_result(result: Dict[str, Any]) -> Dict[str, Any]:
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        cards = data.get("cards") if isinstance(data.get("cards"), list) else []
        raw_items: List[Dict[str, Any]] = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            content = card.get("content")
            if not (isinstance(content, list) and content):
                continue
            dict_content = [item for item in content if isinstance(item, dict)]
            if not dict_content:
                continue
            if any(item.get("word") or item.get("query") for item in dict_content):
                raw_items = dict_content
                break
            nested = dict_content[0].get("content")
            if isinstance(nested, list):
                raw_items = [item for item in nested if isinstance(item, dict)]
                break
        items: List[Dict[str, Any]] = []
        for index, item in enumerate(raw_items):
            title = str(item.get("word") or item.get("query") or item.get("title") or "").strip()
            if not title:
                continue
            hot = str(item.get("hotScore") or item.get("hot_value") or item.get("hot") or item.get("newHotName") or item.get("labelTagName") or "")
            description = str(item.get("desc") or item.get("description") or "")
            image = TianApiService._proxied_baidu_image_url(str(item.get("img") or item.get("image") or item.get("pic") or item.get("picUrl") or ""))
            url = str(item.get("url") or item.get("appUrl") or item.get("rawUrl") or item.get("mobilUrl") or "")
            if not url:
                url = f"https://m.baidu.com/s?word={quote(title)}&sa=fyb_news"
            items.append({
                "rank": len(items) + 1,
                "title": title,
                "hot": hot,
                "description": description,
                "image": image,
                "url": url,
                "raw": dict(item),
            })
        return {
            "platform": "baidu",
            "title": TianApiService._hot_search_title("baidu"),
            "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": items,
        }

    @staticmethod
    async def _get_baidu_top_search() -> Dict[str, Any]:
        async with HttpClient(timeout=15) as client:
            result = await client.get(BAIDU_TOP_API, params={"platform": "pc", "tab": "realtime"})
        if result.get("success") is True:
            data = TianApiService._normalize_baidu_top_api_result(result)
            if data["items"]:
                return {"code": 200, "msg": "success", "data": data}
        return {"code": 200, "msg": result.get("msg") or result.get("error") or "百度热搜接口暂不可用", "fallback": True, "data": TianApiService._empty_hot_search("baidu")}

    @staticmethod
    async def get_hot_search(platform: str = "weibo") -> Dict[str, Any]:
        """微博热搜榜 / 百度热搜榜。"""
        endpoint_map = {
            "weibo": "/weibohot/index",
            "baidu": "/baiduhot/index",
        }
        platform = platform if platform in endpoint_map else "weibo"
        if not settings.TIANAPI_KEY:
            return {"code": 200, "msg": "success", "fallback": True, "data": TianApiService._empty_hot_search(platform)}
        result = await TianApiService._request(
            endpoint_map[platform],
            cache_key=make_cache_key("hot_search", platform=platform),
            cache_ttl=settings.CACHE_TTL_DEFAULT,
        )
        if result.get("code") == 200:
            data = TianApiService._normalize_hot_search_result(platform, result)
            if data["items"]:
                return {"code": 200, "msg": "success", "data": data}
        if platform == "baidu":
            return await TianApiService._get_baidu_top_search()
        return {"code": 200, "msg": result.get("msg") or "热搜接口暂不可用", "fallback": True, "data": TianApiService._empty_hot_search(platform)}
