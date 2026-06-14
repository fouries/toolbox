import asyncio

from api.news_detail import NewsDetailService


class DummyCache:
    store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        self.store[key] = value


class DummyHttpClient:
    calls = []
    response_text = ""

    def __init__(self, *args, **kwargs):
        pass

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

    DummyCache.store = {}
    DummyHttpClient.calls = []
    DummyHttpClient.response_text = ""
    news_detail.cache = DummyCache()
    news_detail.HttpClient = DummyHttpClient


def test_news_detail_fetches_sanitizes_and_caches_article_body():
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
    assert result["data"]["sourceUrl"] == "https://example.com/news/1"
    assert "第一段新闻正文" in result["data"]["content"]
    assert "第二段新闻正文" in result["data"]["content"]
    assert "alert" not in result["data"]["content"]
    assert "display:none" not in result["data"]["content"]
    assert "fromCache" not in result["data"]
    assert cached["data"]["fromCache"] is True
    assert len(DummyHttpClient.calls) == 1


def test_news_detail_rejects_unsafe_urls():
    result = run(NewsDetailService.fetch_detail("javascript:alert(1)"))

    assert result["code"] == 400
    assert "无效" in result["msg"]


if __name__ == "__main__":
    setup_module(None)
    test_news_detail_fetches_sanitizes_and_caches_article_body()
    setup_module(None)
    test_news_detail_rejects_unsafe_urls()
    print("news detail service tests passed")
