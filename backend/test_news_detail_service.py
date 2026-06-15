import asyncio
import shutil
import tempfile
from pathlib import Path

from api.news_detail import NewsDetailService


class DummyCache:
    store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        self.store[key] = value


class DummyHttpClient:
    calls = []
    init_kwargs = []
    response_text = ""

    def __init__(self, *args, **kwargs):
        self.__class__.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def get_text(self, url, headers=None):
        self.__class__.calls.append((url, headers or {}))
        return self.__class__.response_text


def run(coro):
    return asyncio.run(coro)


def setup_module(module):
    import api.news_detail as news_detail

    global _tmp_news_dir
    previous_tmp_dir = globals().get("_tmp_news_dir")
    if previous_tmp_dir:
        shutil.rmtree(previous_tmp_dir, ignore_errors=True)

    DummyCache.store = {}
    DummyHttpClient.calls = []
    DummyHttpClient.init_kwargs = []
    DummyHttpClient.response_text = ""
    _tmp_news_dir = Path(tempfile.mkdtemp(prefix="news-local-test-"))
    news_detail.NewsDetailService.LOCAL_DETAIL_DIR = _tmp_news_dir
    news_detail.NewsDetailService.LOCAL_DETAIL_ROUTE = "/api/news/local"
    news_detail.cache = DummyCache()
    news_detail.HttpClient = DummyHttpClient


def teardown_module(module):
    tmp_dir = globals().get("_tmp_news_dir")
    if tmp_dir:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_news_detail_fetch_writes_local_resource_snapshot():
    html = """
    <html>
      <head>
        <title>原网页标题</title>
        <meta name="description" content="页面简介">
        <script>alert('bad')</script>
        <style>.ad{display:none}</style>
      </head>
      <body>
        <article>
          <h1>AI 新闻标题</h1>
          <p>第一段新闻正文，包含足够多的有效内容。</p>
          <p>第二段新闻正文，继续补充新闻详情。</p>
          <a href="https://example.com/more">相关阅读</a>
        </article>
      </body>
    </html>
    """
    DummyHttpClient.response_text = html

    result = run(NewsDetailService.fetch_detail("https://example.com/news/1"))
    cached = run(NewsDetailService.fetch_detail("https://example.com/news/1"))

    assert result["code"] == 200
    assert result["data"]["title"] == "AI 新闻标题"
    assert result["data"]["localId"]
    assert result["data"]["localUrl"] == f"/api/news/local/{result['data']['localId']}"
    assert result["data"]["sourceUrl"] == "https://example.com/news/1"
    local_path = NewsDetailService.LOCAL_DETAIL_DIR / f"{result['data']['localId']}.json"
    assert local_path.exists()
    assert "第一段新闻正文" in local_path.read_text(encoding="utf-8")
    assert "fromCache" not in result["data"]
    assert cached["data"]["fromCache"] is True
    assert cached["data"]["localId"] == result["data"]["localId"]
    assert cached["data"]["localUrl"] == result["data"]["localUrl"]
    assert len(DummyHttpClient.calls) == 1


def test_news_detail_extracts_original_article_image_and_proxies_it():
    html = """
    <html>
      <head>
        <meta property="og:image" content="/images/article-cover.jpg">
      </head>
      <body>
        <article>
          <h1>带图新闻标题</h1>
          <p>这是一篇带有原文图片的新闻正文，内容足够用于详情页展示。</p>
        </article>
      </body>
    </html>
    """
    DummyCache.store = {}
    DummyHttpClient.calls = []
    DummyHttpClient.response_text = html

    result = run(NewsDetailService.fetch_detail("https://example.com/news/with-image"))

    assert result["code"] == 200
    assert result["data"]["originalImage"] == "https://example.com/images/article-cover.jpg"
    assert result["data"]["image"] == "https://quan1234.com/api/news/image-proxy?url=https%3A%2F%2Fexample.com%2Fimages%2Farticle-cover.jpg"
    local_path = NewsDetailService.LOCAL_DETAIL_DIR / f"{result['data']['localId']}.json"
    assert '"image"' in local_path.read_text(encoding="utf-8")


def test_news_detail_rejects_unsafe_urls():
    result = run(NewsDetailService.fetch_detail("javascript:alert(1)"))

    assert result["code"] == 400
    assert "无效" in result["msg"]


def test_news_detail_http_client_is_created_with_redirect_following_enabled():
    html = """
    <html><body><article><p>重定向后的新闻正文内容，足够用于详情页展示。</p></article></body></html>
    """
    DummyHttpClient.response_text = html
    DummyHttpClient.init_kwargs = []

    result = run(NewsDetailService.fetch_detail("https://example.com/news/redirect"))

    assert result["code"] == 200
    assert DummyHttpClient.init_kwargs[-1]["follow_redirects"] is True


def test_news_detail_prefers_article_body_container_over_comment_article():
    html = """
    <html>
      <body>
        <h1>电竞新闻标题</h1>
        <div id="artibody">
          <p>全体召唤师集合！英雄联盟手游再次联合NBA搞大事啦！</p>
          <p>作为两大竞技领域的强强联手，本次联动将篮球赛场的竞技精神融入召唤师峡谷。</p>
        </div>
        <article class="comment">
          <h2>热门评论（0）</h2>
          <ul><li>暂无评论~~</li></ul>
        </article>
      </body>
    </html>
    """

    detail = NewsDetailService._build_detail("https://dj.sina.com.cn/article/demo.shtml", html)

    assert "全体召唤师集合" in detail["content"]
    assert "竞技精神" in detail["content"]
    assert "热门评论" not in detail["content"]
    assert "暂无评论" not in detail["content"]


if __name__ == "__main__":
    setup_module(None)
    test_news_detail_fetch_writes_local_resource_snapshot()
    setup_module(None)
    test_news_detail_extracts_original_article_image_and_proxies_it()
    setup_module(None)
    test_news_detail_rejects_unsafe_urls()
    setup_module(None)
    test_news_detail_http_client_is_created_with_redirect_following_enabled()
    setup_module(None)
    test_news_detail_prefers_article_body_container_over_comment_article()
    print("news detail service tests passed")
