import hashlib
import html
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin, urlparse

from config import get_settings
from utils.cache import cache
from utils.http_client import HttpClient
from utils.url_security import is_public_http_url

settings = get_settings()


class _ReadableHtmlParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "iframe", "svg", "canvas"}
    BLOCK_TAGS = {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self.headings: List[str] = []
        self._skip_depth = 0
        self._heading_tag: Optional[str] = None
        self._heading_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in {"h1", "h2"}:
            self._heading_tag = tag
            self._heading_parts = []
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == self._heading_tag:
            heading = _normalize_space("".join(self._heading_parts))
            if heading:
                self.headings.append(heading)
            self._heading_tag = None
            self._heading_parts = []
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str):
        if self._skip_depth:
            return
        if self._heading_tag:
            self._heading_parts.append(data)
        else:
            self.parts.append(data)


class NewsDetailService:
    """抓取、清洗并缓存第三方新闻正文，供小程序原生详情页展示。"""

    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    )
    LOCAL_DETAIL_DIR = Path(__file__).resolve().parents[1] / "data" / "news_detail"
    LOCAL_DETAIL_ROUTE = "/api/news/local"

    @staticmethod
    def _local_id(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _local_url(local_id: str) -> str:
        return f"{NewsDetailService.LOCAL_DETAIL_ROUTE}/{local_id}"

    @staticmethod
    def _cache_key(url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return f"news-detail:{digest}"

    @staticmethod
    def _normalize_source_url(url: str) -> str:
        url = str(url or "").strip()
        if url.startswith("//"):
            return f"https:{url}"
        return url

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        return is_public_http_url(NewsDetailService._normalize_source_url(url))

    @staticmethod
    def _extract_meta(html_text: str, name: str) -> str:
        pattern = re.compile(
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        match = pattern.search(html_text)
        if match:
            return html.unescape(match.group(1)).strip()
        pattern = re.compile(
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
            re.IGNORECASE,
        )
        match = pattern.search(html_text)
        return html.unescape(match.group(1)).strip() if match else ""

    @staticmethod
    def _extract_title(html_text: str, headings: List[str]) -> str:
        for meta_name in ("og:title", "twitter:title"):
            title = NewsDetailService._extract_meta(html_text, meta_name)
            if title:
                return _normalize_space(title)
        if headings:
            return headings[0]
        match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
        if match:
            return _normalize_space(re.sub(r"<[^>]+>", "", html.unescape(match.group(1))))
        return "新闻详情"

    @staticmethod
    def _extract_source(html_text: str, url: str) -> str:
        for meta_name in ("og:site_name", "source", "author"):
            source = NewsDetailService._extract_meta(html_text, meta_name)
            if source:
                return _normalize_space(source)
        return urlparse(url).netloc

    @staticmethod
    def _extract_publish_time(html_text: str) -> str:
        for meta_name in ("article:published_time", "pubdate", "publishdate"):
            value = NewsDetailService._extract_meta(html_text, meta_name)
            if value:
                return _normalize_space(value)
        match = re.search(r"20\d{2}[-年/]\d{1,2}[-月/]\d{1,2}(?:[日\s]+\d{1,2}:\d{2}(?::\d{2})?)?", html_text)
        return _normalize_space(match.group(0)) if match else ""

    @staticmethod
    def _proxied_image_url(image_url: str) -> str:
        image_url = str(image_url or "").strip()
        if not image_url:
            return ""
        return f"https://quan1234.com/api/news/image-proxy?url={quote(image_url, safe='')}"

    @staticmethod
    def _normalize_image_url(image_url: str, page_url: str = "") -> str:
        image_url = html.unescape(str(image_url or "")).strip()
        if not image_url:
            return ""
        if image_url.startswith("//"):
            return f"https:{image_url}"
        return urljoin(page_url, image_url)

    @staticmethod
    def _is_placeholder_image(image_url: str) -> bool:
        value = str(image_url or "").lower()
        return any(marker in value for marker in (
            "weixinfixed",
            "empty.png",
            "placeholder",
            "default_logo",
            "logo_",
            "/logo",
            "avatar",
            "s-avatar",
            "certification",
            "favicon",
            ".ico",
            "qrcode",
            "qr-code",
            "ewm.png",
            "zxcode_",
        ))

    @staticmethod
    def _is_netease_article_url(page_url: str) -> bool:
        return (urlparse(page_url).hostname or "").lower().endswith("163.com")

    @staticmethod
    def _image_matches_article_date(html_text: str, image_url: str) -> bool:
        publish_time = NewsDetailService._extract_publish_time(html_text)
        date_match = re.search(r"(20\d{2})[-年/]?(\d{1,2})[-月/]?(\d{1,2})", publish_time or "")
        if not date_match:
            return True
        year = date_match.group(1)
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        expected = {
            f"{year}/{month:02d}{day:02d}",
            f"{year}/{month:02d}/{day:02d}",
            f"{year}%2f{month:02d}{day:02d}",
            f"{year}%2f{month:02d}%2f{day:02d}",
        }
        lower_url = str(image_url or "").lower()
        url_date = re.search(r"20\d{2}(?:/|%2f)(?:\d{4}|\d{2}(?:/|%2f)\d{2})", lower_url)
        if not url_date:
            return True
        return any(token in lower_url for token in expected)

    @staticmethod
    def _is_usable_article_image(html_text: str, page_url: str, image_url: str) -> bool:
        if not image_url or NewsDetailService._is_placeholder_image(image_url):
            return False
        if NewsDetailService._is_netease_article_url(page_url) and not NewsDetailService._image_matches_article_date(html_text, image_url):
            return False
        return True

    @staticmethod
    def _is_preferred_image_trusted(page_url: str, image_url: str) -> bool:
        image_url = str(image_url or "").lower()
        # 网易聚合列表偶尔把不同文章配成同一张 nimg 缩略图；如果原文页没有可验证图片，宁可不展示，也不要错配。
        if NewsDetailService._is_netease_article_url(page_url) and "nimg.ws.126.net" in image_url:
            return False
        return True

    @staticmethod
    def _extract_images(html_text: str, page_url: str, preferred_image: str = "") -> List[str]:
        """提取所有可用的文章图片，最多返回8张（避免过多图片影响体验）"""
        preferred_image = NewsDetailService._normalize_image_url(preferred_image, page_url)
        images: List[str] = []
        
        # 如果有推荐图片，放在第一位
        if (
            preferred_image
            and NewsDetailService.is_safe_image_url(preferred_image)
            and not NewsDetailService._is_placeholder_image(preferred_image)
            and NewsDetailService._is_preferred_image_trusted(page_url, preferred_image)
        ):
            images.append(preferred_image)
        
        source_html = NewsDetailService._extract_main_content_html(html_text)
        # 使用非f-string避免引号转义问题
        img_pattern = re.compile(r'<img([^>]+)>', re.IGNORECASE)
        class_pattern = re.compile(r'class=[\'"]([^\'"]*)[\'"]', re.IGNORECASE)
        
        for match in img_pattern.finditer(source_html):
            if len(images) >= 8:
                break
            attrs = match.group(1)
            
            # 跳过头像、logo、认证等无关图片
            class_match = class_pattern.search(attrs)
            if class_match:
                class_val = class_match.group(1).lower()
                if any(k in class_val for k in ('avatar', 'author', 'certification', 'comment', 'logo')):
                    continue
            
            # 查找图片URL
            found_url = None
            for attr_name in ("data-src", "data-original", "data-url", "src"):
                pattern = re.compile(attr_name + r'=[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
                attr_match = pattern.search(attrs)
                if attr_match:
                    found_url = attr_match.group(1)
                    break
            
            if not found_url:
                continue
                
            image_url = NewsDetailService._normalize_image_url(found_url, page_url)
            if (
                NewsDetailService._is_usable_article_image(html_text, page_url, image_url)
                and image_url not in images
            ):
                images.append(image_url)
        
        # 如果还不够，从meta补充
        if len(images) == 0:
            for meta_name in ("og:image", "twitter:image", "twitter:image:src", "image"):
                if len(images) >= 8:
                    break
                value = NewsDetailService._extract_meta(html_text, meta_name)
                if value:
                    image_url = NewsDetailService._normalize_image_url(value, page_url)
                    if (
                        NewsDetailService._is_usable_article_image(html_text, page_url, image_url)
                        and image_url not in images
                    ):
                        images.append(image_url)
        
        return images

    @staticmethod
    def _extract_image(html_text: str, page_url: str, preferred_image: str = "") -> str:
        """保留兼容旧接口：只返回第一张图片"""
        images = NewsDetailService._extract_images(html_text, page_url, preferred_image)
        return images[0] if images else ""

    @staticmethod
    def is_safe_image_url(url: str) -> bool:
        return NewsDetailService._is_safe_url(url)

    @staticmethod
    async def fetch_image(url: str) -> Dict[str, Any]:
        url = (url or "").strip()
        if not NewsDetailService.is_safe_image_url(url):
            return {"code": 400, "msg": "无效或不安全的图片链接"}
        try:
            async with HttpClient(timeout=10, follow_redirects=False) as client:
                if client._client is None:
                    return {"code": 502, "msg": "图片读取失败"}
                response = await client._client.get(url, headers={"User-Agent": NewsDetailService.USER_AGENT})
                response.raise_for_status()
            content_type = response.headers.get("content-type", "image/jpeg")
            if not content_type.startswith("image/"):
                return {"code": 400, "msg": "URL 不是图片"}
            return {"code": 200, "content": response.content, "content_type": content_type}
        except Exception:
            return {"code": 502, "msg": "图片读取失败"}

    @staticmethod
    def _extract_main_content_html(html_text: str) -> str:
        container_patterns = [
            r'<div[^>]+class=["\'][^"\']*detailPage-layout-bottom[^"\']*["\'][^>]*>(.*?)(?:</div><!--\[-->|<div[^>]+class=["\'][^"\']*footer|</body>)',
            r'<div[^>]+class=["\'][^"\']*news_html[^"\']*["\'][^>]*>(.*?)(?:</div>\s*</div>|</body>)',
            r'<div[^>]+id=["\']artibody["\'][^>]*>(.*?)(?:<div[^>]+class=["\'][^"\']*article_share|<article\b[^>]*class=["\'][^"\']*comment|</section>)',
            r'<div[^>]+class=["\'][^"\']*(?:article-content|article_content|article-body|main-content)[^"\']*["\'][^>]*>(.*?)</div>',
            r'<article\b(?![^>]+class=["\'][^"\']*comment)[^>]*>(.*?)</article>',
        ]
        for pattern in container_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        return html_text

    @staticmethod
    def _extract_content(html_text: str) -> str:
        source_html = NewsDetailService._extract_main_content_html(html_text)
        parser = _ReadableHtmlParser()
        parser.feed(source_html)
        lines = [_normalize_space(line) for line in "".join(parser.parts).splitlines()]
        lines = [line for line in lines if len(line) >= 2]
        
        # 过滤掉作者信息、编辑、责编、来源、版权等杂项内容
        filtered_lines = []
        # 常见媒体来源作者信息行基本都是短行，包含媒体名称+时间+地点+作者
        # 这里收集所有常见媒体相关关键词，只要短行包含这些关键词就过滤掉
        media_keywords = [
            '作者', '编辑', '责编', '记者', '来源', '原标题', '原题',
            '中新经纬', '网易', '网易号', '公众号', '官方号', '客户端',
            '央视网', '人民网', '新华网', '人民日报', '澎湃新闻', '新京报',
            '新浪', '搜狐', '腾讯网', '凤凰网', '界面新闻', '封面新闻',
            '新华社', '中新网', '中国新闻网', '北京日报', '广州日报',
            '解放日报', '经济日报', '证券时报', '中国证券报',
            '证券日报', '第一财经', '财新', '每日经济新闻',
            '经济参考报', '环球网', '环球时报', '中国日报',
            '央视', '网', '报', '社', '客户端', '公众号', '官方',
        ]
        
        skip_patterns = [
            r'^作者[:：]',
            r'^编辑[:：]',
            r'^责编[:：]',
            r'^来源[:：]',
            r'^原标题[:：]',
            r'^原题[:：]',
            r'^本文来源',
            r'^本文编辑',
            r'^责任编辑',
            r'^版权声明',
            r'^点击阅读原文',
            r'^本文网址',
            r'^[本文为]+.*[翻译整理转载]',
            r'^本报记者',
            r'^记者[:：]',
            r'^通讯员',
            r'^撰文',
            r'^摄影',
            r'^视觉设计',
            r'^编辑整理',
        ]
        for line in lines:
            line = _normalize_space(line)
            if not line:
                continue
            line_lower = line.lower()
            # 检查是否匹配明确的跳过模式
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue
            # 更短的行直接过滤（小于10字符，基本上就是地点/作者/来源）
            if len(line) <= 10:
                continue
            # 短行（<35字符）包含任何媒体关键词，直接过滤掉
            if len(line) < 35:
                if any(k in line_lower for k in media_keywords):
                    continue
                # 包含年份或者常见省市名称，也过滤掉（时间地点信息）
                if '202' in line or any(city in line for city in ['北京', '上海', '广州', '深圳', '杭州', '成都', '广东', '江苏', '浙江']):
                    continue
            # 包含年份+冒号（时间）且是短行，包含媒体关键词，过滤掉
            if len(line) < 45 and '202' in line and (':' in line or '-' in line):
                continue
            filtered_lines.append(line)
            
        content = "\n\n".join(filtered_lines)
        return content[:12000]

    @staticmethod
    def _build_detail(url: str, html_text: str, preferred_image: str = "") -> Dict[str, Any]:
        parser = _ReadableHtmlParser()
        parser.feed(html_text)
        title = NewsDetailService._extract_title(html_text, parser.headings)
        content = NewsDetailService._extract_content(html_text)
        description = NewsDetailService._extract_meta(html_text, "description")
        if len(content) < 20 and description:
            content = description
        # 提取所有图片
        images = NewsDetailService._extract_images(html_text, url, preferred_image)
        # 兼容旧字段：第一张图片保持原来位置
        original_image = images[0] if images else ""
        local_id = NewsDetailService._local_id(url)
        
        # 将多张图片均匀插入到正文段落中
        if len(images) > 1:
            # 拆分段落，跳过第一张（已经在标题下展示）
            insert_images = images[1:]
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            num_paragraphs = len(paragraphs)
            num_images = len(insert_images)
            
            if num_paragraphs > 0 and num_images > 0:
                # 计算插入位置：均匀分布 - 在每 N 段后插入一张图片
                # 策略：从正文 1/N, 2/N ... 位置插入，避免在开头和结尾插入过多
                step = num_paragraphs / (num_images + 1)
                positions = [int(step * (i + 1)) - 1 for i in range(num_images)]
                # 确保位置不越界
                positions = [p for p in positions if 0 <= p < num_paragraphs]
                
                # 重建带图片标记的段落
                new_paragraphs = []
                insert_idx = 0
                for idx, para in enumerate(paragraphs):
                    new_paragraphs.append(para)
                    if insert_idx < len(positions) and idx == positions[insert_idx]:
                        # 插入图片标记：<!--IMAGE:索引--> 使用原始图片索引
                        image_idx = 1 + insert_idx  # 因为跳过了第一张
                        new_paragraphs.append(f"<!--IMAGE:{image_idx}-->")
                        insert_idx += 1
                
                content = "\n\n".join(new_paragraphs)
        
        detail = {
            "title": title,
            "source": NewsDetailService._extract_source(html_text, url),
            "publishTime": NewsDetailService._extract_publish_time(html_text),
            "description": _normalize_space(description),
            "content": content,
            "images": [NewsDetailService._proxied_image_url(img) for img in images],  # 所有代理后的图片URL列表
            "sourceUrl": url,
            "localId": local_id,
            "localUrl": NewsDetailService._local_url(local_id),
            "cachedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "detailVersion": 6,  # 升级版本
        }
        if original_image:
            detail["originalImage"] = original_image
            detail["image"] = NewsDetailService._proxied_image_url(original_image)
        return detail

    @staticmethod
    def _local_path(local_id: str) -> Path:
        safe_id = re.sub(r"[^a-f0-9]", "", str(local_id or ""))[:64]
        return NewsDetailService.LOCAL_DETAIL_DIR / f"{safe_id}.json"

    @staticmethod
    def _write_local_detail(detail: Dict[str, Any]) -> None:
        local_id = str(detail.get("localId") or "")
        if not local_id:
            return
        NewsDetailService.LOCAL_DETAIL_DIR.mkdir(parents=True, exist_ok=True)
        path = NewsDetailService._local_path(local_id)
        path.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def read_local_detail(local_id: str) -> Dict[str, Any]:
        path = NewsDetailService._local_path(local_id)
        if not path.exists():
            return {"code": 404, "msg": "本地新闻资源不存在或已过期"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"code": 500, "msg": "本地新闻资源读取失败"}
        return {"code": 200, "msg": "success", "data": {**data, "fromLocal": True}}

    @staticmethod
    async def fetch_detail(url: str, preferred_image: str = "") -> Dict[str, Any]:
        url = NewsDetailService._normalize_source_url(url)
        if not NewsDetailService._is_safe_url(url):
            return {"code": 400, "msg": "无效或不安全的新闻链接"}

        cache_key = NewsDetailService._cache_key(url)
        has_preferred_image = bool(NewsDetailService._normalize_image_url(preferred_image, url))
        normalized_preferred_image = NewsDetailService._normalize_image_url(preferred_image, url)
        cached = await cache.get(cache_key)
        if cached and cached.get("detailVersion") == 6 and (not has_preferred_image or cached.get("originalImage") == normalized_preferred_image):
            return {"code": 200, "msg": "success", "data": {**cached, "fromCache": True}}

        try:
            async with HttpClient(timeout=12, follow_redirects=False) as client:
                html_text = await client.get_text(
                    url,
                    headers={
                        "User-Agent": NewsDetailService.USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
            detail = NewsDetailService._build_detail(url, html_text, preferred_image=preferred_image)
            if not detail["content"]:
                return {"code": 502, "msg": "未能提取新闻正文，请复制原文链接到浏览器打开"}
            NewsDetailService._write_local_detail(detail)
            await cache.set(cache_key, detail, settings.CACHE_TTL_DEFAULT * 12)
            return {"code": 200, "msg": "success", "data": detail}
        except Exception:
            return {"code": 502, "msg": "新闻正文抓取失败，请复制原文链接到浏览器打开"}


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()
