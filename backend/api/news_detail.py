import hashlib
import html
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from config import get_settings
from utils.cache import cache
from utils.http_client import HttpClient

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
        self.parts.append(data)


class NewsDetailService:
    """抓取、清洗并缓存第三方新闻正文，供小程序原生详情页展示。"""

    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    )

    @staticmethod
    def _cache_key(url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return f"news-detail:{digest}"

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc:
            return False
        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
            return False
        if host.startswith("10.") or host.startswith("192.168."):
            return False
        if re.match(r"^172\.(1[6-9]|2\d|3[0-1])\.", host):
            return False
        return True

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
    def _extract_content(html_text: str) -> str:
        article_match = re.search(r"<article\b[^>]*>(.*?)</article>", html_text, re.IGNORECASE | re.DOTALL)
        source_html = article_match.group(1) if article_match else html_text
        parser = _ReadableHtmlParser()
        parser.feed(source_html)
        lines = [_normalize_space(line) for line in "".join(parser.parts).splitlines()]
        lines = [line for line in lines if len(line) >= 2]
        content = "\n\n".join(lines)
        return content[:12000]

    @staticmethod
    def _build_detail(url: str, html_text: str) -> Dict[str, Any]:
        parser = _ReadableHtmlParser()
        parser.feed(html_text)
        title = NewsDetailService._extract_title(html_text, parser.headings)
        content = NewsDetailService._extract_content(html_text)
        description = NewsDetailService._extract_meta(html_text, "description")
        if len(content) < 20 and description:
            content = description
        return {
            "title": title,
            "source": NewsDetailService._extract_source(html_text, url),
            "publishTime": NewsDetailService._extract_publish_time(html_text),
            "description": _normalize_space(description),
            "content": content,
            "sourceUrl": url,
            "cachedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    async def fetch_detail(url: str) -> Dict[str, Any]:
        url = (url or "").strip()
        if not NewsDetailService._is_safe_url(url):
            return {"code": 400, "msg": "无效或不安全的新闻链接"}

        cache_key = NewsDetailService._cache_key(url)
        cached = await cache.get(cache_key)
        if cached:
            return {"code": 200, "msg": "success", "data": {**cached, "fromCache": True}}

        try:
            async with HttpClient(timeout=12, follow_redirects=True) as client:
                html_text = await client.get_text(
                    url,
                    headers={
                        "User-Agent": NewsDetailService.USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
            detail = NewsDetailService._build_detail(url, html_text)
            if not detail["content"]:
                return {"code": 502, "msg": "未能提取新闻正文，请复制原文链接到浏览器打开"}
            await cache.set(cache_key, detail, settings.CACHE_TTL_DEFAULT * 12)
            return {"code": 200, "msg": "success", "data": detail}
        except Exception:
            return {"code": 502, "msg": "新闻正文抓取失败，请复制原文链接到浏览器打开"}


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()
