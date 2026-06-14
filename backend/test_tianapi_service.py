import asyncio

from api.tianapi import TianApiService


class DummyCache:
    async def get(self, key):
        return None

    async def set(self, key, value, ttl=300):
        return None


class DummyHttpClient:
    calls = []
    responses = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def get(self, url, params=None):
        self.__class__.calls.append((url, params or {}))
        path = url.replace('https://apis.tianapi.com', '')
        key = (path, (params or {}).get('code'))
        return self.__class__.responses.get(key) or self.__class__.responses.get((path, None)) or {"code": 404, "msg": "missing mock"}


def run(coro):
    return asyncio.run(coro)


def setup_module(module):
    import api.tianapi as tianapi

    tianapi.cache = DummyCache()
    tianapi.HttpClient = DummyHttpClient
    setattr(tianapi.settings, 'TIANAPI_KEY', 'test-' + 'key')
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}


def test_news_endpoints_use_real_paths_and_normalize_nested_newslist():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"curpage": 1, "allnum": 1, "newslist": [{"title": "internet"}]}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"curpage": 1, "allnum": 1, "list": [{"title": "esports"}]}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"curpage": 1, "allnum": 1, "newslist": [{"title": "auto"}]}},
    }

    internet = run(TianApiService.get_info_news('internet'))
    esports = run(TianApiService.get_info_news('esports'))
    auto = run(TianApiService.get_info_news('auto'))

    paths = [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls]
    assert paths == ['/internet/index', '/esports/index', '/auto/index']
    assert internet['newslist'] == [{"title": "internet"}]
    assert esports['newslist'] == [{"title": "esports"}]
    assert auto['newslist'] == [{"title": "auto"}]
    assert all(call[1].get('num') == '10' for call in DummyHttpClient.calls)
    assert all(call[1].get('form') == '1' for call in DummyHttpClient.calls)


def test_gold_endpoint_sends_kinds_and_normalizes_market_fields():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/gold/index', None): {"code": 200, "msg": "success", "result": {"list": [{"code": "au9999", "latestprice": 329.02, "rafvalue": -2.47, "raf": -0.74, "updatetime": "2019-11-09 02:28:55"}]}}
    }

    result = run(TianApiService.get_gold_price())

    assert DummyHttpClient.calls[0][0].endswith('/gold/index')
    assert DummyHttpClient.calls[0][1]['kinds']
    assert result['newslist'][0]['name'] == 'Au99.99 黄金'
    assert result['newslist'][0]['price'] == '329.02'
    assert result['newslist'][0]['unit'] == '元/克'
    assert result['newslist'][0]['updown'] == '-2.47 (-0.74%)'
    assert result['newslist'][0]['time'] == '2019-11-09 02:28:55'


def test_gold_fallback_is_not_renormalized_when_api_key_is_missing():
    import api.tianapi as tianapi

    DummyHttpClient.calls = []
    original_key = tianapi.settings.TIANAPI_KEY
    try:
        tianapi.settings.TIANAPI_KEY = ''
        result = run(TianApiService.get_gold_price())
    finally:
        tianapi.settings.TIANAPI_KEY = original_key

    assert DummyHttpClient.calls == []
    assert result['fallback'] is True
    assert result['newslist'][0]['name'] == '国内黄金'
    assert result['newslist'][1]['unit'] == '美元/盎司'


def test_crude_endpoint_queries_wti_and_blt_and_normalizes_market_fields():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/crude/index', 'wti'): {"code": 200, "msg": "success", "result": {"name": "WTI原油(NYMEX原油)", "diffnum": "0.2", "diffrate": "0.36%", "nowprice": 57.444, "updatetime": "2019-11-09 05:59:57"}},
        ('/crude/index', 'blt'): {"code": 200, "msg": "success", "result": {"name": "布伦特原油", "diffnum": "0.3", "diffrate": "0.48%", "nowprice": 62.1, "updatetime": "2019-11-09 05:59:57"}},
    }

    result = run(TianApiService.get_crude_oil())

    assert [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls] == ['/crude/index', '/crude/index']
    assert [call[1]['code'] for call in DummyHttpClient.calls] == ['wti', 'blt']
    assert result['newslist'][0]['name'] == 'WTI原油(NYMEX原油)'
    assert result['newslist'][0]['price'] == '57.444'
    assert result['newslist'][0]['unit'] == '美元/桶'
    assert result['newslist'][0]['updown'] == '0.2 (0.36%)'
    assert result['newslist'][0]['time'] == '2019-11-09 05:59:57'
    assert len(result['newslist']) == 2


def test_daily_brief_endpoint_uses_bulletin_and_normalizes_lines():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/bulletin/index', None): {"code": 200, "msg": "success", "result": {"list": ["1、今日要闻", "2、财经动态"], "ctime": "2026-06-14"}}
    }

    result = run(TianApiService.get_daily_brief())

    assert DummyHttpClient.calls[0][0].endswith('/bulletin/index')
    assert result['data']['date'] == '2026-06-14'
    assert result['data']['items'][0]['title'] == '今日要闻'
    assert result['data']['items'][0]['rank'] == 1
    assert result['data']['items'][1]['title'] == '财经动态'


def test_hot_search_endpoint_uses_weibo_and_baidu_paths_and_normalizes_items():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/weibohot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"hotword": "微博话题", "hotwordnum": "123456", "word_scheme": "微博话题"}]}},
        ('/baiduhot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"word": "百度话题", "hotScore": "9999", "desc": "话题摘要", "url": "https://m.baidu.com/s?word=test"}]}},
    }

    weibo = run(TianApiService.get_hot_search('weibo'))
    baidu = run(TianApiService.get_hot_search('baidu'))

    assert [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls] == ['/weibohot/index', '/baiduhot/index']
    assert weibo['data']['platform'] == 'weibo'
    assert weibo['data']['items'][0]['title'] == '微博话题'
    assert weibo['data']['items'][0]['hot'] == '123456'
    assert weibo['data']['items'][0]['url'].startswith('https://s.weibo.com/weibo')
    assert baidu['data']['platform'] == 'baidu'
    assert baidu['data']['items'][0]['title'] == '百度话题'
    assert baidu['data']['items'][0]['description'] == '话题摘要'
    assert baidu['data']['items'][0]['url'] == 'https://m.baidu.com/s?word=test'


def test_hot_search_detail_builds_content_from_keyword_and_related_news():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": [
            {"title": "无关科技新闻", "description": "普通资讯", "source": "科技", "url": "https://example.com/tech"},
            {"title": "微博话题 引发关注", "description": "网友正在讨论微博话题的最新进展", "source": "互联网", "url": "https://example.com/topic"},
        ]}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='weibo',
        keyword='微博话题',
        hot='123456',
        description='话题摘要',
        url='https://s.weibo.com/weibo?q=test',
    ))

    assert [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls] == ['/internet/index', '/esports/index', '/auto/index']
    assert result['code'] == 200
    assert result['data']['platform'] == 'weibo'
    assert result['data']['keyword'] == '微博话题'
    assert result['data']['sourceUrl'] == 'https://s.weibo.com/weibo?q=test'
    assert '微博话题' in result['data']['summary']
    assert '微博话题' in result['data']['content']
    assert result['data']['sections']
    assert result['data']['relatedNews'][0]['title'] == '微博话题 引发关注'


def test_baidu_fallback_hot_detail_does_not_show_unavailable_message():
    fallback = TianApiService._fallback_hot_search('baidu')
    assert fallback['items']
    assert all('接口暂不可用' not in item['description'] for item in fallback['items'])

    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }

    for item in fallback['items'][:4]:
        result = run(TianApiService.get_hot_search_detail(
            platform='baidu',
            keyword=item['title'],
            hot=item['hot'],
            description='热搜接口暂不可用，展示备用热点分类。',
            url=item['url'],
        ))
        text = result['data']['summary'] + result['data']['content']
        assert result['code'] == 200
        assert item['title'] in text
        assert '热搜接口暂不可用' not in text
        assert '接口暂不可用' not in text
        assert result['data']['sections']


if __name__ == '__main__':
    setup_module(None)
    for test in [
        test_news_endpoints_use_real_paths_and_normalize_nested_newslist,
        test_gold_endpoint_sends_kinds_and_normalizes_market_fields,
        test_gold_fallback_is_not_renormalized_when_api_key_is_missing,
        test_crude_endpoint_queries_wti_and_blt_and_normalizes_market_fields,
        test_daily_brief_endpoint_uses_bulletin_and_normalizes_lines,
        test_hot_search_endpoint_uses_weibo_and_baidu_paths_and_normalizes_items,
        test_hot_search_detail_builds_content_from_keyword_and_related_news,
        test_baidu_fallback_hot_detail_does_not_show_unavailable_message,
    ]:
        setup_module(None)
        test()
    print('tianapi service contract tests passed')
