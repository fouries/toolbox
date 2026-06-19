import json
import re
import html
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import quote, urljoin, unquote, urlparse, parse_qs
from utils.http_client import HttpClient
from utils.cache import cache, make_cache_key
from config import get_settings
from api.news_detail import NewsDetailService

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
        hot = str(item.get("hotwordnum") or item.get("hotScore") or item.get("index") or item.get("num") or item.get("hot") or "")
        description = TianApiService._clean_hot_description(str(item.get("desc") or item.get("brief") or item.get("description") or ""))
        url = str(item.get("url") or item.get("mobilUrl") or "")
        image = TianApiService._proxied_baidu_image_url(str(item.get("img") or item.get("image") or item.get("pic") or item.get("picUrl") or item.get("avatar") or item.get("cover") or ""))
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
            "image": image,
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
            num=20,
            form=1,
            fallback=TianApiService._fallback_news(category)
        )

    @staticmethod
    def _strip_html_tags(value: str) -> str:
        value = re.sub(r"<script[\s\S]*?</script>", " ", str(value or ""), flags=re.IGNORECASE)
        value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.IGNORECASE)
        value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
        value = re.sub(r"<[^>]+>", " ", value)
        value = html.unescape(value)
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _clean_search_title(value: str) -> str:
        value = re.sub(r"<!--/?red_(?:beg|end)-->", "", str(value or ""))
        return TianApiService._strip_html_tags(value)

    @staticmethod
    def _clean_search_description(value: str) -> str:
        value = re.sub(r"<!--/?red_(?:beg|end)-->", "", str(value or ""))
        value = re.sub(r"^\s*\d{4}年\d{1,2}月\d{1,2}日\s*[-—－]?\s*", "", value)
        return TianApiService._strip_html_tags(value)

    @staticmethod
    def _parse_sogou_news_results(text: str, keyword: str, limit: int = 8) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        seen_titles = set()
        blocks = re.findall(r"<div[^>]+class=[\"'][^\"']*(?:vrwrap|result)[^\"']*[\"'][^>]*>[\s\S]*?(?=<div[^>]+class=[\"'][^\"']*(?:vrwrap|result)[^\"']*[\"']|</body>|$)", text or "", flags=re.IGNORECASE)
        if not blocks:
            blocks = re.findall(r"<h3[\s\S]*?</h3>[\s\S]{0,1200}", text or "", flags=re.IGNORECASE)
        for block in blocks:
            title_match = re.search(r"<h3[^>]*>[\s\S]*?<a[^>]*href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>", block, flags=re.IGNORECASE)
            if not title_match:
                continue
            title = TianApiService._clean_search_title(title_match.group(2))
            if not title or title in seen_titles or "推荐您搜索" in title:
                continue
            desc_match = re.search(r"<div[^>]+class=[\"'][^\"']*(?:space-txt|str-text-info|ft|fz-mid)[^\"']*[\"'][^>]*>([\s\S]*?)</div>", block, flags=re.IGNORECASE)
            description = TianApiService._clean_search_description(desc_match.group(1)) if desc_match else ""
            if not description and keyword not in title:
                continue
            source_match = re.search(r"<div[^>]+class=[\"'][^\"']*citeurl[^\"']*[\"'][^>]*>([\s\S]*?)</div>", block, flags=re.IGNORECASE)
            source = TianApiService._strip_html_tags(source_match.group(1)) if source_match else "搜狗搜索"
            href = html.unescape(title_match.group(1))
            url = urljoin("https://www.sogou.com/", href)
            results.append({
                "title": title,
                "description": description,
                "source": source,
                "ctime": "",
                "url": url,
            })
            seen_titles.add(title)
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _parse_bing_news_results(text: str, keyword: str, limit: int = 8) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        seen_titles = set()
        blocks = re.findall(
            r"<li[^>]+class=[\"'][^\"']*b_algo[^\"']*[\"'][^>]*>[\s\S]*?(?=<li[^>]+class=[\"'][^\"']*b_algo|</ol>|</body>|$)",
            text or "",
            flags=re.IGNORECASE,
        )
        for block in blocks:
            title_match = re.search(r"<h2[^>]*>[\s\S]*?<a[^>]*href=[\"']([^\"']+)[\"'][^>]*>([\s\S]*?)</a>", block, flags=re.IGNORECASE)
            if not title_match:
                continue
            title = TianApiService._clean_search_title(title_match.group(2))
            if not title or title in seen_titles:
                continue
            desc_match = re.search(r"<div[^>]+class=[\"'][^\"']*b_caption[^\"']*[\"'][^>]*>[\s\S]*?<p[^>]*>([\s\S]*?)</p>", block, flags=re.IGNORECASE)
            description = TianApiService._clean_search_description(desc_match.group(1)) if desc_match else ""
            description = TianApiService._strip_leading_repeated_title(title, description)
            if not description and keyword not in title:
                continue
            source_match = re.search(r"<cite[^>]*>([\s\S]*?)</cite>", block, flags=re.IGNORECASE)
            source = TianApiService._strip_html_tags(source_match.group(1)) if source_match else "必应搜索"
            href = html.unescape(title_match.group(1))
            results.append({
                "title": title,
                "description": description,
                "source": source,
                "ctime": "",
                "url": href,
            })
            seen_titles.add(title)
            if len(results) >= limit:
                break
        return results

    @staticmethod
    async def _fetch_keyword_news(keyword: str, limit: int = 8) -> List[Dict[str, str]]:
        keyword = str(keyword or "").strip()
        if not keyword:
            return []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            async with HttpClient(timeout=15, follow_redirects=True) as client:
                text = await client.get_text(
                    "https://www.sogou.com/sogou",
                    params={"query": keyword, "ie": "utf8"},
                    headers=headers,
                )
                results = TianApiService._parse_sogou_news_results(text, keyword, limit=limit)
                if results:
                    return results
                text = await client.get_text(
                    "https://www.bing.com/search",
                    params={"q": keyword},
                    headers=headers,
                )
        except Exception:
            return []
        return TianApiService._parse_bing_news_results(text, keyword, limit=limit)

    @staticmethod
    def _longest_common_substring_length(left: str, right: str) -> int:
        left = str(left or "")
        right = str(right or "")
        if not left or not right:
            return 0
        previous = [0] * (len(right) + 1)
        best = 0
        for left_char in left:
            current = [0]
            for index, right_char in enumerate(right, start=1):
                value = previous[index - 1] + 1 if left_char == right_char else 0
                current.append(value)
                if value > best:
                    best = value
            previous = current
        return best

    @staticmethod
    def _score_related_news(keyword: str, item: Dict[str, Any]) -> int:
        text = f"{item.get('title') or ''} {item.get('description') or ''} {item.get('source') or ''}".lower()
        keyword_text = keyword.lower().strip()
        if not keyword_text:
            return 0
        score = 0
        if keyword_text in text:
            score += 10
        else:
            common_length = TianApiService._longest_common_substring_length(keyword_text, text)
            if common_length >= 4:
                score += min(common_length, 8)
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
    def _strip_leading_repeated_title(title: str, description: str) -> str:
        title_clean = TianApiService._strip_html_tags(title)
        description = TianApiService._strip_html_tags(description)
        if not title_clean or not description:
            return description
        normalized_title = re.sub(r"\s+", "", title_clean)
        normalized_desc = re.sub(r"\s+", "", description)
        title_variants = {
            normalized_title,
            re.sub(r"[_\-—|].*$", "", normalized_title),
        }
        for variant in sorted(title_variants, key=len, reverse=True):
            if len(variant) >= 6 and normalized_desc.startswith(variant):
                prefix_end = 0
                compact = ""
                for index, char in enumerate(description):
                    if char.isspace():
                        continue
                    compact += char
                    if len(compact) >= len(variant):
                        prefix_end = index + 1
                        break
                remainder = description[prefix_end:].lstrip(" _-—:：，,。\n\t")
                if remainder:
                    return remainder
        return description

    @staticmethod
    def _clean_hot_description(description: str) -> str:
        description = html.unescape(str(description or "")).strip()
        # 只去掉末尾的“查看更多”，保留前面的内容
        description = re.sub(r"\s*查看更多\s*>?\s*$", "", description).strip()
        # 只有当整个desc都是不可用标记时才返回空
        unavailable_markers = ("热搜接口暂不可用", "接口暂不可用", "展示备用热点分类")
        if any(marker in description for marker in unavailable_markers):
            # 如果除了不可用标记之外还有其他内容，保留其他内容
            for marker in unavailable_markers:
                description = description.replace(marker, "").strip()
        # 只要有内容就保留，不要因为短就返回空
        if len(description) < 5:
            return ""
        return description

    @staticmethod
    def _is_incomplete_hot_description(description: str) -> bool:
        description = TianApiService._strip_html_tags(html.unescape(str(description or ""))).strip()
        if not description:
            return True
        if not TianApiService._clean_hot_description(description):
            return True
        # 百度热榜列表经常把摘要截成 “…… 查看更多>”，这种摘要在详情页显得不完整。
        return bool(re.search(r"(?:\.{3,}|…|⋯)\s*(?:查看更多\s*>?)?\s*$", description))

    @staticmethod
    def _trim_incomplete_hot_description(description: str) -> str:
        description = TianApiService._clean_hot_description(description)
        if not description or not TianApiService._is_incomplete_hot_description(description):
            return description
        base = re.sub(r"\s*(?:\.{3,}|…|⋯).*?$", "", description).strip()
        if not base:
            return ""
        punctuation_positions = [base.rfind(mark) for mark in ("。", "！", "？", "!", "?", "；", ";")]
        last_punctuation = max(punctuation_positions)
        if last_punctuation >= 10:
            return base[: last_punctuation + 1].strip()
        return base if len(base) >= 20 else ""

    @staticmethod
    def _hot_description_mentions_keyword(keyword: str, description: str) -> bool:
        keyword = re.sub(r"\s+", "", str(keyword or ""))
        description = re.sub(r"\s+", "", TianApiService._strip_html_tags(str(description or "")))
        if not keyword or not description:
            return False
        if keyword in description:
            return True
        terms = {keyword[i:i + 2] for i in range(max(0, len(keyword) - 1))}
        terms = {term for term in terms if len(term) == 2 and term not in {"一个", "这些", "相关", "新闻", "热搜"}}
        return sum(1 for term in terms if term in description) >= 1

    @staticmethod
    def _prefer_complete_hot_description(current: str, candidate: str) -> str:
        current_clean = TianApiService._clean_hot_description(current)
        candidate_clean = TianApiService._clean_hot_description(candidate)
        if not candidate_clean:
            return TianApiService._trim_incomplete_hot_description(current_clean)
        if not current_clean:
            return TianApiService._trim_incomplete_hot_description(candidate_clean) or candidate_clean
        candidate_complete = not TianApiService._is_incomplete_hot_description(candidate_clean)
        current_incomplete = TianApiService._is_incomplete_hot_description(current_clean)
        if current_incomplete and candidate_complete:
            return candidate_clean
        if candidate_complete and len(candidate_clean) >= len(current_clean) + 8:
            return candidate_clean
        candidate_trimmed = TianApiService._trim_incomplete_hot_description(candidate_clean)
        current_trimmed = TianApiService._trim_incomplete_hot_description(current_clean)
        if current_incomplete and candidate_trimmed and len(candidate_trimmed) >= len(current_trimmed):
            return candidate_trimmed
        return current_trimmed if current_incomplete and current_trimmed else current_clean

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
    def _normalize_video_url(value: Any) -> str:
        url = html.unescape(str(value or "")).replace("\\/", "/").strip()
        if not url:
            return ""
        try:
            url = unquote(url)
        except Exception:
            pass
        if url.startswith("//"):
            url = f"https:{url}"
        if url.startswith("http://") and any(host in url for host in ("bdstatic.com", "baidu.com", "bcebos.com")):
            url = "https://" + url[len("http://"):]
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            return ""
        if not re.search(r"\.(?:mp4|m3u8)(?:\?|$)", url, flags=re.IGNORECASE):
            return ""
        return url


    @staticmethod
    def _proxy_baidu_video_url(video_url: str) -> str:
        if not video_url:
            return ""
        return f"https://quan1234.com/api/video-proxy?url={quote(video_url, safe='')}"

    @staticmethod
    def _normalize_video_poster(value: Any) -> str:
        url = html.unescape(str(value or "")).replace("\\/", "/").strip()
        if not url:
            return ""
        try:
            url = unquote(url)
        except Exception:
            pass
        if url.startswith("//"):
            url = f"https:{url}"
        return url if re.match(r"^https?://", url, flags=re.IGNORECASE) else ""

    @staticmethod
    def _collect_video_candidates(value: Any, videos: List[Dict[str, str]], seen: set, title: str = "") -> None:
        if len(videos) >= 3:
            return
        if isinstance(value, dict):
            candidate_title = title
            for key, item in value.items():
                if str(key).lower() in {"title", "text"} and not candidate_title:
                    candidate_title = TianApiService._strip_html_tags(str(item))[:80]
            candidates: List[Dict[str, str]] = []
            for item in value.get("clarityUrl") or []:
                if isinstance(item, dict):
                    video_url = TianApiService._normalize_video_url(item.get("url"))
                    if video_url:
                        candidates.append({
                            "src": video_url,
                            "rank": str(item.get("rank") if item.get("rank") is not None else "99"),
                            "title": str(item.get("title") or ""),
                        })
            if candidates:
                try:
                    candidates.sort(key=lambda item: int(item.get("rank") or "99"))
                except Exception:
                    pass
                first_candidate = candidates[0]
                seen_key = first_candidate["src"].split("?", 1)[0]
                if seen_key not in seen:
                    videos.append({
                        "url": TianApiService._proxy_baidu_video_url(first_candidate["src"]),
                        "originalUrl": first_candidate["src"],
                        "poster": TianApiService._normalize_video_poster(value.get("poster") or value.get("cover") or value.get("image")),
                        "title": candidate_title or first_candidate.get("title") or title,
                    })
                    seen.add(seen_key)
                if len(videos) >= 3:
                    return
            src = ""
            poster = ""
            for key, item in value.items():
                key_lower = str(key).lower()
                if key_lower in {"src", "url", "videourl", "media_url", "mediaurl"} or "videourl" in key_lower:
                    src = src or TianApiService._normalize_video_url(item)
                elif key_lower in {"poster", "cover", "image", "img", "thumbnail"} or "poster" in key_lower:
                    poster = poster or TianApiService._normalize_video_poster(item)
                elif key_lower in {"title", "text"} and not candidate_title:
                    candidate_title = TianApiService._strip_html_tags(str(item))[:80]
            seen_key = src.split("?", 1)[0] if src else ""
            if src and seen_key not in seen:
                videos.append({"url": TianApiService._proxy_baidu_video_url(src), "originalUrl": src, "poster": poster, "title": candidate_title})
                seen.add(seen_key)
            for item in value.values():
                TianApiService._collect_video_candidates(item, videos, seen, candidate_title)
                if len(videos) >= 3:
                    return
        elif isinstance(value, list):
            for item in value:
                TianApiService._collect_video_candidates(item, videos, seen, title)
                if len(videos) >= 3:
                    return
        elif isinstance(value, str):
            src = TianApiService._normalize_video_url(value)
            seen_key = src.split("?", 1)[0] if src else ""
            if src and seen_key not in seen:
                videos.append({"url": TianApiService._proxy_baidu_video_url(src), "originalUrl": src, "poster": "", "title": title})
                seen.add(seen_key)

    @staticmethod
    def _extract_video_resources_from_text(text: str, limit: int = 3) -> List[Dict[str, str]]:
        text = str(text or "")
        videos: List[Dict[str, str]] = []
        seen = set()
        for pattern in (
            r'"video"\s*:\s*({[\s\S]{0,6000}?})\s*,\s*"control"',
            r'"videoData"\s*:\s*({[\s\S]{0,12000}?})\s*,\s*"contentData"',
            r'"autoplayInfo"\s*:\s*({[\s\S]{0,12000}?})\s*,\s*"control"',
        ):
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if len(videos) >= limit:
                    break
                raw_json = html.unescape(match.group(1)).replace('\\/', '/')
                try:
                    parsed = json.loads(raw_json)
                except Exception:
                    continue
                TianApiService._collect_video_candidates(parsed, videos, seen)
            if len(videos) >= limit:
                break
        if len(videos) < limit:
            for match in re.finditer(r'https?:\\?/\\?/[^"\'<>\s]+?\.(?:mp4|m3u8)(?:\?[^"\'<>\s]*)?', text, flags=re.IGNORECASE):
                src = TianApiService._normalize_video_url(match.group(0))
                seen_key = src.split("?", 1)[0] if src else ""
                if src and seen_key not in seen:
                    videos.append({"url": TianApiService._proxy_baidu_video_url(src), "originalUrl": src, "poster": "", "title": ""})
                    seen.add(seen_key)
                    if len(videos) >= limit:
                        break
        if len(videos) > 1:
            preferred: List[Dict[str, str]] = []
            fallback: List[Dict[str, str]] = []
            for video in videos:
                original = str(video.get("originalUrl") or "")
                if re.search(r"/(?:hd|sc|1080p|720p|540p|480p|360p)/", original, flags=re.IGNORECASE):
                    fallback.append(video)
                else:
                    preferred.append(video)
            if preferred:
                videos = preferred + fallback
        return videos[:limit]

    @staticmethod
    def _extract_video_page_cards(text: str, limit: int = 6) -> List[Dict[str, str]]:
        """Extract structured cards from Baidu mobile video result pages.

        The `/sf/vsearch?...&atn=index` page can expose `title`, `loc`,
        `videoSrc`, and preview poster in JSON-ish blobs without using the
        older `autoplayInfo`/`curVideoMeta` wrappers. Keep this extraction
        source-limited to Baidu-owned video result pages; callers still run
        `_video_page_matches_keyword` on each card before accepting a video.
        """
        text = html.unescape(str(text or "")).replace("\\/", "/")
        cards: List[Dict[str, str]] = []
        seen = set()
        for match in re.finditer(r'"videoSrc"\s*:\s*"([^"<>]+)"', text, flags=re.IGNORECASE):
            if len(cards) >= limit:
                break
            src = TianApiService._normalize_video_url(match.group(1))
            seen_key = src.split("?", 1)[0] if src else ""
            if not src or seen_key in seen:
                continue
            start = max(0, match.start() - 3000)
            end = min(len(text), match.end() + 1600)
            context = text[start:end]
            title_match = re.search(r'"title"\s*:\s*"([^"<>]{2,160})"', context, flags=re.IGNORECASE)
            loc_match = re.search(r'"loc"\s*:\s*"(https?://[^"<>]+)"', context, flags=re.IGNORECASE)
            poster_match = re.search(r'"poster"\s*:\s*"(https?://[^"<>]+)"', context, flags=re.IGNORECASE)
            title = TianApiService._strip_html_tags(title_match.group(1))[:120] if title_match else ""
            source_url = html.unescape(loc_match.group(1)).strip() if loc_match else ""
            poster = TianApiService._normalize_video_poster(poster_match.group(1)) if poster_match else ""
            cards.append({
                "url": TianApiService._proxy_baidu_video_url(src),
                "originalUrl": src,
                "poster": poster,
                "title": title,
                "sourceUrl": source_url,
                "_context": context,
            })
            seen.add(seen_key)
        return cards

    @staticmethod
    def _extract_haokan_video_page_urls(text: str, limit: int = 3) -> List[str]:
        text = html.unescape(str(text or "")).replace("\\/", "/")
        urls: List[str] = []
        seen = set()
        for pattern in (
            r'data-mdurl=["\'](https?://haokan\.baidu\.com/v\?[^"\']+)["\']',
            r'https?://haokan\.baidu\.com/v\?[^"\'<>\s]+',
        ):
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                url = match.group(1) if match.groups() else match.group(0)
                url = html.unescape(url).strip()
                parsed = urlparse(url)
                if parsed.netloc != "haokan.baidu.com":
                    continue
                dedupe_key = url.split("#", 1)[0]
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                urls.append(url)
                if len(urls) >= limit:
                    return urls
        return urls

    @staticmethod
    def _extract_baidu_video_landing_urls(text: str, limit: int = 3) -> List[str]:
        text = html.unescape(str(text or "")).replace("\\/", "/")
        urls: List[str] = []
        seen = set()
        for pattern in (
            r'https?://mbd\.baidu\.com/newspage/data/videolanding\?[^"\'<>\s]+',
            r'url=["\'](https?%3A%2F%2Fmbd\.baidu\.com%2Fnewspage%2Fdata%2Fvideolanding%3F[^"\']+)["\']',
            r'src["\']?\s*:\s*["\'](https?://mbd\.baidu\.com/newspage/data/videolanding\?[^"\']+)["\']',
        ):
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                url = match.group(1) if match.groups() else match.group(0)
                try:
                    url = unquote(url)
                except Exception:
                    pass
                url = html.unescape(url).strip()
                parsed = urlparse(url)
                if parsed.netloc != "mbd.baidu.com" or parsed.path != "/newspage/data/videolanding":
                    continue
                dedupe_key = url.split("#", 1)[0]
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                urls.append(url)
                if len(urls) >= limit:
                    return urls
        return urls

    @staticmethod
    def _video_page_matches_keyword(keyword: str, text: str) -> bool:
        keyword = str(keyword or "").strip()
        if not keyword:
            return False
        original = html.unescape(str(text or ""))
        try:
            decoded = original.encode("utf-8", errors="ignore").decode("unicode_escape", errors="ignore")
        except Exception:
            decoded = ""
        haystack = f"{original} {decoded}".lower()
        compact_haystack = re.sub(r"\s+", "", haystack)
        compact_keyword = re.sub(r"\s+", "", keyword.lower())
        if compact_keyword and compact_keyword in compact_haystack:
            return True
        # 百度热搜词和好看视频标题经常是同一事件的不同写法，例如
        # “顶流演员竟然没戏拍了吗” vs “顶流演员也没戏拍了？...在线求工作”。
        # 该视频页必须先从热搜原链接/百度普通搜索页抽到；这里再用关键词片段做保守校验。
        terms = [compact_keyword[i:i + 2] for i in range(max(0, len(compact_keyword) - 1))]
        stop_terms = {"一个", "这些", "相关", "新闻", "热搜", "了吗", "怎么", "什么", "为何"}
        terms = [term for term in terms if len(term) == 2 and term not in stop_terms]
        matched_terms = {term for term in terms if term in compact_haystack}
        if len(matched_terms) >= 3 and len(matched_terms) >= max(3, len(set(terms)) // 3):
            return True
        keyword_words = re.findall(r"[\u4e00-\u9fff]{2,}", compact_keyword)
        if keyword_words:
            matched_chars = sum(len(word) for word in keyword_words if word and word in compact_haystack)
            if matched_chars >= max(4, min(len(compact_keyword), 12) // 2):
                return True
        score = 0
        for term in ("今年", "端午", "60年", "六十年"):
            if term in keyword and term.lower() in haystack:
                score += 1
        return score >= 2

    @staticmethod
    async def _fetch_baidu_hot_videos(keyword: str, source_url: str = "", limit: int = 1) -> List[Dict[str, str]]:
        keyword = str(keyword or "").strip()
        if not keyword:
            return []
        search_url = "https://m.baidu.com/s"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        # 百度移动普通搜索现在经常把服务端请求导向 wappass 图形验证。
        # 实测视频垂搜页对 Android Chrome UA 仍返回包含 videoSrc 的结果页，
        # iPhone Safari UA 则也会触发验证，导致所有视频提取为空。
        video_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://m.baidu.com/",
        }
        try:
            async with HttpClient(timeout=15, follow_redirects=True) as client:
                source_url = str(source_url or "").strip()
                candidate_pages: List[Tuple[str, Dict[str, str], Dict[str, str]]] = []
                source_word = keyword
                if source_url.startswith("http"):
                    candidate_pages.append((source_url, {}, headers))
                    parsed_source = urlparse(source_url)
                    if parsed_source.netloc.endswith("baidu.com") and parsed_source.path == "/s":
                        source_query = parse_qs(parsed_source.query)
                        source_word = str((source_query.get("wd") or source_query.get("word") or [keyword])[0] or keyword)
                        # 有些热搜原链接直接访问会触发安全验证，但同一个百度普通搜索
                        # 模板（非视频垂搜）可以返回原搜索结果里的好看视频卡片。
                        candidate_pages.append(("https://www.baidu.com/s", {"wd": source_word, "tn": "baiduhome_pg"}, headers))
                candidate_pages.append((search_url, {"word": keyword, "sa": "fyb_news"}, headers))

                video_pages: List[str] = []
                collected: List[Dict[str, str]] = []
                seen_original = set()

                async def collect_from_text(text_result: str, allow_inline_video_cards: bool = False) -> bool:
                    videos = TianApiService._extract_video_resources_from_text(text_result, limit=limit)
                    if allow_inline_video_cards:
                        videos = TianApiService._extract_video_page_cards(text_result, limit=max(limit * 3, 6)) or videos
                    for video in videos:
                        if allow_inline_video_cards:
                            haystack = " ".join(str(video.get(field) or "") for field in ("title", "sourceUrl", "_context"))
                            if not TianApiService._video_page_matches_keyword(keyword, haystack):
                                continue
                        original_url = str(video.get("originalUrl") or video.get("url") or "")
                        seen_key = original_url.split("?", 1)[0]
                        if seen_key and seen_key not in seen_original:
                            seen_original.add(seen_key)
                            video.pop("_context", None)
                            collected.append(video)
                            if len(collected) >= limit:
                                return True
                    for haokan_url in TianApiService._extract_haokan_video_page_urls(text_result, limit=3):
                        if haokan_url not in video_pages:
                            video_pages.append(haokan_url)
                    for landing_url in TianApiService._extract_baidu_video_landing_urls(text_result, limit=3):
                        if landing_url not in video_pages:
                            video_pages.append(landing_url)
                    return False

                candidate_results = await asyncio.gather(
                    *(client.get_text(page_url, params=params, headers=page_headers) for page_url, params, page_headers in candidate_pages),
                    return_exceptions=True,
                )
                for text_result in candidate_results:
                    if isinstance(text_result, BaseException):
                        continue
                    if await collect_from_text(text_result):
                        return collected[:limit]

                # 百度普通搜索在服务器侧经常被重定向到“百度安全验证”。移动端视频
                # 结果页 `/sf/vsearch?...&atn=index` 目前不触发该验证，并且页面内
                # 直接包含 `videoSrc`、标题、落地页和封面。仅作为兜底，并继续用
                # 标题/落地页上下文做关键词校验，避免把泛搜索视频错配到热搜详情。
                if not video_pages:
                    video_search_text = await client.get_text(
                        "https://m.baidu.com/sf/vsearch",
                        params={"pd": "video", "word": source_word or keyword, "tn": "vsearch", "atn": "index"},
                        headers=video_headers,
                    )
                    if await collect_from_text(video_search_text, allow_inline_video_cards=True):
                        return collected[:limit]

                video_page_results = await asyncio.gather(
                    *(client.get_text(page_url, headers=video_headers) for page_url in video_pages[:3]),
                    return_exceptions=True,
                )
                for page_text in video_page_results:
                    if isinstance(page_text, BaseException):
                        continue
                    if not TianApiService._video_page_matches_keyword(keyword, page_text):
                        continue
                    for video in TianApiService._extract_video_resources_from_text(page_text, limit=limit):
                        original_url = str(video.get("originalUrl") or video.get("url") or "")
                        seen_key = original_url.split("?", 1)[0]
                        if seen_key and seen_key not in seen_original:
                            seen_original.add(seen_key)
                            collected.append(video)
                            if len(collected) >= limit:
                                return collected[:limit]
                return collected[:limit]
        except Exception:
            return []
        return []

    @staticmethod
    def _build_hot_raw_section(platform_name: str, keyword: str, hot: str, desc_text: str, raw_item: Dict[str, Any]) -> Dict[str, str]:
        title = str(raw_item.get("word") or raw_item.get("hotword") or raw_item.get("title") or raw_item.get("keyword") or keyword)
        heat = str(raw_item.get("hotScore") or raw_item.get("hotwordnum") or raw_item.get("num") or raw_item.get("hot") or hot or "--")
        raw_desc = TianApiService._clean_hot_description(str(raw_item.get("desc") or raw_item.get("description") or ""))
        desc = TianApiService._prefer_complete_hot_description(raw_desc, desc_text)
        parts = [f"平台：{platform_name}", f"关键词：{title}"]
        if heat:
            parts.append(f"热度：{heat}")
        if desc:
            parts.append(f"接口摘要：{desc}")
        return {"title": f"{platform_name}返回信息", "body": "\n".join(parts)}

    @staticmethod
    async def _materialize_related_news(items: List[Dict[str, str]], limit: int = 0) -> List[Dict[str, str]]:
        # 不再提前抓取新闻详情，等用户真的点击新闻时再抓取，这样加载热搜详情会快很多
        return items

    @staticmethod
    async def _fetch_hot_detail_images(keyword: str, related_news: List[Dict[str, Any]], limit: int = 3) -> List[str]:
        """从强匹配相关新闻原文里提取正文图片，用于原文主体是长图的百度热搜。"""
        images: List[str] = []
        seen = set()
        for item in related_news[:3]:
            url = str(item.get("url") or "").strip()
            if not url or TianApiService._score_related_news(keyword, item) < 2:
                continue
            if not NewsDetailService._is_safe_url(url):
                continue
            try:
                detail_result = await NewsDetailService.fetch_detail(url, preferred_image=str(item.get("picUrl") or ""))
            except Exception:
                continue
            if detail_result.get("code") != 200 or not isinstance(detail_result.get("data"), dict):
                continue
            for image_url in detail_result["data"].get("images") or []:
                image_url = str(image_url or "").strip()
                if image_url and image_url not in seen:
                    seen.add(image_url)
                    images.append(image_url)
                    if len(images) >= limit:
                        return images
        return images

    @staticmethod
    def _build_hot_search_detail(
        platform: str,
        keyword: str,
        hot: str = "",
        description: str = "",
        url: str = "",
        related_news: Optional[List[Dict[str, Any]]] = None,
        raw_item: Optional[Dict[str, Any]] = None,
        videos: Optional[List[Dict[str, str]]] = None,
        images: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        platform = platform if platform in {"weibo", "baidu"} else "baidu"
        platform_name = TianApiService._hot_search_title(platform)
        related_news = related_news or []
        title = f"{keyword} - 热搜详情" if keyword else "热搜详情"
        hot_text = f"，当前热度为 {hot}" if hot else ""
        raw_item = raw_item or {}
        videos = videos or []
        images = images or []
        raw_desc = str(raw_item.get("brief") or raw_item.get("desc") or raw_item.get("description") or "")
        # 优先用传入的description，再用raw里的desc/brief，最后才用fallback
        hot_desc = TianApiService._clean_hot_description(description)
        if not hot_desc:
            # 尝试不严格clean，只去掉HTML和查看更多
            temp_desc = html.unescape(str(description or raw_desc or "")).strip()
            temp_desc = re.sub(r"\s*查看更多\s*>?\s*$", "", temp_desc).strip()
            if len(temp_desc) >= 5:
                hot_desc = temp_desc
        if not hot_desc:
            # 再尝试raw_desc的temp版本
            temp_desc = html.unescape(str(raw_desc or "")).strip()
            temp_desc = re.sub(r"\s*查看更多\s*>?\s*$", "", temp_desc).strip()
            if len(temp_desc) >= 5:
                hot_desc = temp_desc
        desc_text = hot_desc
        first_item_desc = ""
        if related_news and len(related_news) > 0:
            first_item_desc = str(related_news[0].get("description") or "").strip()
            first_item_desc = re.sub(r"<[^>]+>", "", first_item_desc).strip()
            if first_item_desc and not TianApiService._hot_description_mentions_keyword(keyword, first_item_desc):
                first_item_desc = ""
        if first_item_desc:
            desc_text = TianApiService._prefer_complete_hot_description(desc_text, first_item_desc)
        # 长图新闻的搜索摘要常只有“统筹/文案/设计/新华社出品”等署名信息，
        # 不能用这类署名覆盖百度官方给出的正文摘要。
        if re.fullmatch(r"[\s\S]{0,80}(?:统筹|文案|设计|制作|出品|来源|编辑|作者|记者|新媒体中心)[\s\S]{0,80}", desc_text or ""):
            desc_text = hot_desc or raw_desc
        desc_text = TianApiService._trim_incomplete_hot_description(desc_text) or desc_text
        if not desc_text:
            desc_text = TianApiService._fallback_hot_detail_description(platform_name, keyword)

        raw_section = TianApiService._build_hot_raw_section(platform_name, keyword, hot, desc_text, raw_item)
        news_content_lines = []
        seen_content_lines = set()
        seen_descriptions = set()
        for item in related_news[:8]:
            item_title = TianApiService._strip_html_tags(str(item.get("title") or "")).strip()
            item_desc = TianApiService._strip_html_tags(str(item.get("description") or "")).strip()
            if TianApiService._is_incomplete_hot_description(item_title):
                item_title = ""
            if TianApiService._is_incomplete_hot_description(item_desc):
                item_desc = ""
            if item_desc and not TianApiService._hot_description_mentions_keyword(keyword, item_desc):
                item_desc = ""
            # 正文区域只放有完整摘要的相关新闻；标题本身不是正文，避免出现“...但难活的可不止这8家”这类残缺标题行。
            if not item_desc:
                continue
            desc_key = re.sub(r"\s+", "", item_desc)
            if desc_key in seen_descriptions:
                continue
            seen_descriptions.add(desc_key)
            line = f"{item_title}：{item_desc}" if item_title else item_desc
            line = TianApiService._trim_incomplete_hot_description(line) or line
            if TianApiService._is_incomplete_hot_description(line):
                continue
            line_key = re.sub(r"\s+", "", line)
            if line_key in seen_content_lines:
                continue
            seen_content_lines.add(line_key)
            news_content_lines.append(line)
            if len(news_content_lines) >= 5:
                break
        news_content = "\n".join(news_content_lines)
        if news_content_lines:
            # desc_text 已经在上方从热搜摘要和首条相关新闻中择优，并会裁掉明显截断的 “...” 尾巴。
            summary = desc_text
            if hot and keyword and hot not in summary:
                summary = f"{summary}（热度：{hot}）"
            sections = [{"title": "相关新闻内容", "body": news_content}]
        else:
            summary = desc_text
            if hot and keyword and hot not in summary:
                summary = f"{summary}（热度：{hot}）"
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
            "videos": videos,
            "image": images[0] if images else "",
            "images": images,
            "rawHotItem": raw_item,
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    @staticmethod
    async def get_hot_search_detail(
        platform: str = "baidu",
        keyword: str = "",
        hot: str = "",
        description: str = "",
        url: str = "",
        raw: str = "",
    ) -> Dict[str, Any]:
        """百度热搜详情：生成关键词、图片和摘要所需的结构化内容。"""
        keyword = str(keyword or "").strip()
        platform = "baidu"
        
        # 先尝试从缓存获取。media 版本号需要在视频/图片提取或缓存策略变化时递增，
        # 避免 Redis 长时间返回旧的空视频结果。
        cache_key = make_cache_key("hot_search_detail", platform=platform, keyword=keyword, media="video_sources_v16_android_vsearch_no_related_card_desc_v9_images_short_empty")
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        raw_item_for_desc = TianApiService._parse_hot_raw(raw)
        raw_desc_for_check = str(raw_item_for_desc.get("brief") or raw_item_for_desc.get("desc") or raw_item_for_desc.get("description") or raw or "")
        is_baidu_source = str(url or "").startswith(("https://www.baidu.com/", "https://m.baidu.com/"))
        original_desc_incomplete = TianApiService._is_incomplete_hot_description(description) or (
            not TianApiService._clean_hot_description(description)
            and TianApiService._is_incomplete_hot_description(raw_desc_for_check)
        )
        official_desc_complete = False
        if is_baidu_source and original_desc_incomplete:
            official = await TianApiService._get_baidu_top_search_data()
            for official_item in official.get("items") or []:
                if not isinstance(official_item, dict):
                    continue
                if str(official_item.get("title") or "").strip() != keyword:
                    continue
                official_desc = str(official_item.get("description") or "")
                official_desc_complete = bool(
                    TianApiService._clean_hot_description(official_desc)
                    and not TianApiService._is_incomplete_hot_description(official_desc)
                )
                description = TianApiService._prefer_complete_hot_description(
                    description or raw_desc_for_check,
                    official_desc,
                )
                break

        all_news: List[Dict[str, Any]] = []
        # 检查是否有可用的description，如果有就不用去调用三个资讯接口了，直接快速返回。
        # 如果原始摘要是“... 查看更多>”一类截断文本，不能把裁剪后的半句当作完整正文，
        # 除非百度官方接口明确给了完整 desc；否则继续查强匹配相关新闻来补正文。
        cleaned_desc_for_check = TianApiService._clean_hot_description(description) or TianApiService._clean_hot_description(raw_desc_for_check)
        has_hot_desc = bool(
            cleaned_desc_for_check
            and not TianApiService._is_incomplete_hot_description(cleaned_desc_for_check)
            and (not original_desc_incomplete or official_desc_complete)
        )
        
        matched: List[Dict[str, Any]] = []
        if not has_hot_desc:
            # 相关资讯卡片已下线。只在摘要不完整时保留强匹配资讯查找，
            # 用于补全正文/提取可信详情图；不再为了展示“相关资讯”额外请求外部来源。
            tasks = [TianApiService.get_info_news(category) for category in ("internet", "esports", "auto")]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result.get("code") == 200 and isinstance(result.get("newslist"), list):
                    all_news.extend(item for item in result["newslist"] if isinstance(item, dict))

            scored = []
            for item in all_news:
                normalized = TianApiService._normalize_related_news(item)
                if not normalized["title"]:
                    continue
                scored.append((TianApiService._score_related_news(keyword, normalized), normalized))

            matched = [
                item
                for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True)
                if score >= 2
            ]
            if not matched:
                keyword_news = await TianApiService._fetch_keyword_news(keyword, limit=8)
                matched = [
                    item
                    for item in keyword_news
                    if TianApiService._score_related_news(keyword, item) >= 2
                ]
            matched = await TianApiService._materialize_related_news(matched[:8])
        # 视频识别和长图提取都会访问外部页面，彼此不依赖；并发执行可减少首次打开详情的等待时间。
        video_task = TianApiService._fetch_baidu_hot_videos(keyword, source_url=str(url or ""), limit=1) if platform == "baidu" else asyncio.sleep(0, result=[])
        image_task = TianApiService._fetch_hot_detail_images(keyword, matched[:8], limit=3) if is_baidu_source and matched else asyncio.sleep(0, result=[])
        video_result, image_result = await asyncio.gather(video_task, image_task, return_exceptions=True)
        videos: List[Dict[str, str]]
        images: List[str]
        if isinstance(video_result, BaseException):
            videos = []
        else:
            videos = video_result
        if isinstance(image_result, BaseException):
            images = []
        else:
            images = image_result
        data = TianApiService._build_hot_search_detail(
            platform=platform,
            keyword=keyword,
            hot=str(hot or ""),
            description=str(description or ""),
            url=str(url or ""),
            related_news=matched[:8],
            raw_item=TianApiService._parse_hot_raw(raw),
            videos=videos,
            images=images,
        )
        if platform == "baidu":
            data["relatedNews"] = []
        result = {"code": 200, "msg": "success", "data": data}
        
        # 缓存成功的富媒体结果 1 小时；空视频/空图片结果只短缓存，避免百度安全验证等瞬时失败卡住恢复。
        detail_ttl = 600 if not videos and not images else 3600
        await cache.set(cache_key, result, ttl=detail_ttl)
        return result

    @staticmethod
    async def get_hot_search_detail_basic(
        platform: str = "baidu",
        keyword: str = "",
        hot: str = "",
        description: str = "",
        url: str = "",
        raw: str = "",
    ) -> Dict[str, Any]:
        """百度热搜轻详情：只使用列表随带字段，避免阻塞首屏。"""
        keyword = str(keyword or "").strip()
        platform = "baidu"

        cache_key = make_cache_key("hot_search_detail_basic", platform=platform, keyword=keyword, desc=description, media="basic_v2_no_image")
        cached = await cache.get(cache_key)
        if cached:
            return cached

        raw_item = TianApiService._parse_hot_raw(raw)
        raw_desc = str(raw_item.get("brief") or raw_item.get("desc") or raw_item.get("description") or raw or "")
        quick_description = TianApiService._prefer_complete_hot_description(str(description or ""), raw_desc)
        data = TianApiService._build_hot_search_detail(
            platform=platform,
            keyword=keyword,
            hot=str(hot or ""),
            description=quick_description,
            url=str(url or ""),
            related_news=[],
            raw_item=raw_item,
            videos=[],
            images=[],
        )
        result = {"code": 200, "msg": "success", "data": data}
        await cache.set(cache_key, result, ttl=3600)
        return result

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
            description = TianApiService._clean_hot_description(str(item.get("desc") or item.get("description") or ""))
            image = TianApiService._proxied_baidu_image_url(str(item.get("img") or item.get("image") or item.get("pic") or item.get("picUrl") or item.get("avatar") or item.get("cover") or ""))
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
    def _merge_baidu_official_media(primary: Dict[str, Any], official: Dict[str, Any]) -> Dict[str, Any]:
        """用百度官方热榜补全天行 /nethot 缺失的图片和原链接，仅标题严格匹配时使用。"""
        primary_items = primary.get("items") if isinstance(primary.get("items"), list) else []
        official_items = official.get("items") if isinstance(official.get("items"), list) else []
        if not primary_items or not official_items:
            return primary
        official_by_title = {str(item.get("title") or "").strip(): item for item in official_items if isinstance(item, dict)}
        for index, item in enumerate(primary_items):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            official_item = official_by_title.get(title)
            if not official_item:
                continue
            if not item.get("image") and official_item.get("image"):
                item["image"] = official_item["image"]
            default_search_url = f"https://m.baidu.com/s?word={quote(title)}&sa=fyb_news" if title else ""
            if official_item.get("url") and (not item.get("url") or item.get("url") == default_search_url):
                item["url"] = official_item["url"]
            if official_item.get("description"):
                item["description"] = TianApiService._prefer_complete_hot_description(
                    str(item.get("description") or ""),
                    str(official_item.get("description") or ""),
                )
        return primary

    @staticmethod
    async def _get_baidu_top_search_data() -> Dict[str, Any]:
        async with HttpClient(timeout=15) as client:
            result = await client.get(BAIDU_TOP_API, params={"platform": "pc", "tab": "realtime"})
        if result.get("success") is True:
            return TianApiService._normalize_baidu_top_api_result(result)
        return {"platform": "baidu", "title": TianApiService._hot_search_title("baidu"), "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"), "items": []}

    @staticmethod
    async def _get_baidu_top_search() -> Dict[str, Any]:
        data = await TianApiService._get_baidu_top_search_data()
        if data["items"]:
            return {"code": 200, "msg": "success", "data": data}
        return {"code": 200, "msg": "百度热搜接口暂不可用", "fallback": True, "data": TianApiService._empty_hot_search("baidu")}

    @staticmethod
    async def get_hot_search(platform: str = "baidu") -> Dict[str, Any]:
        """百度热搜榜。"""
        endpoint_map = {
            "baidu": "/nethot/index",
        }
        platform = platform if platform in endpoint_map else "baidu"
        if not settings.TIANAPI_KEY:
            return {"code": 200, "msg": "success", "fallback": True, "data": TianApiService._empty_hot_search(platform)}
        result = await TianApiService._request(
            endpoint_map[platform],
            cache_key=make_cache_key("hot_search", platform=platform, desc="complete_v2"),
            cache_ttl=settings.CACHE_TTL_DEFAULT,
        )
        if result.get("code") == 200:
            data = TianApiService._normalize_hot_search_result(platform, result)
            if data["items"]:
                if platform == "baidu":
                    needs_official_media = any(
                        isinstance(item, dict) and (
                            not item.get("image")
                            or str(item.get("url") or "").startswith("https://m.baidu.com/s?word=")
                            or TianApiService._is_incomplete_hot_description(str(item.get("description") or ""))
                        )
                        for item in data["items"]
                    )
                    if needs_official_media:
                        official = await TianApiService._get_baidu_top_search_data()
                        data = TianApiService._merge_baidu_official_media(data, official)
                return {"code": 200, "msg": "success", "data": data}
        if platform == "baidu":
            return await TianApiService._get_baidu_top_search()
        return {"code": 200, "msg": result.get("msg") or "热搜接口暂不可用", "fallback": True, "data": TianApiService._empty_hot_search(platform)}
