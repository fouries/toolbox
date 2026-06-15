import asyncio
import json

from api.tianapi import TianApiService


class DummyNewsDetailService:
    calls = []

    @staticmethod
    def _is_safe_url(url):
        return str(url or '').startswith('http')

    @staticmethod
    async def fetch_detail(url):
        DummyNewsDetailService.calls.append(url)
        local_id = str(abs(hash(url)))[:8]
        return {"code": 200, "data": {"localId": local_id, "localUrl": f"/api/news/local/{local_id}", "description": "本地化后的新闻正文摘要"}}


class DummyCache:
    async def get(self, key):
        return None

    async def set(self, key, value, ttl=300):
        return None


class DummyHttpClient:
    calls = []
    responses = {}
    text_responses = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def get(self, url, params=None, headers=None):
        self.__class__.calls.append((url, params or {}))
        path = url.replace('https://apis.tianapi.com', '')
        key = (path, (params or {}).get('code'))
        return self.__class__.responses.get(key) or self.__class__.responses.get((path, None)) or {"code": 404, "msg": "missing mock"}

    async def get_text(self, url, params=None, headers=None):
        self.__class__.calls.append((url, params or {}))
        path = url.replace('https://apis.tianapi.com', '')
        key = (path, (params or {}).get('code'))
        if key in self.__class__.text_responses:
            return self.__class__.text_responses[key]
        if (path, None) in self.__class__.text_responses:
            return self.__class__.text_responses[(path, None)]
        return ""


def run(coro):
    return asyncio.run(coro)


def setup_module(module):
    import api.tianapi as tianapi

    tianapi.cache = DummyCache()
    tianapi.HttpClient = DummyHttpClient
    tianapi.NewsDetailService = DummyNewsDetailService
    setattr(tianapi.settings, 'TIANAPI_KEY', 'test-' + 'key')
    DummyNewsDetailService.calls = []
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {}


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


def test_hot_search_endpoint_uses_baidu_nethot_and_normalizes_items():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/nethot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"keyword": "百度话题", "index": "9999", "brief": "话题摘要", "trend": "沸", "picUrl": "https://example.com/hot.png", "url": "https://example.com/hot"}]}},
    }

    weibo_removed = run(TianApiService.get_hot_search('weibo'))
    baidu = run(TianApiService.get_hot_search('baidu'))

    assert [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls] == ['/nethot/index', '/nethot/index']
    assert weibo_removed['data']['platform'] == 'baidu'
    assert weibo_removed['data']['title'] == '百度热搜榜'
    assert baidu['data']['platform'] == 'baidu'
    assert baidu['data']['title'] == '百度热搜榜'
    assert baidu['data']['items'][0]['title'] == '百度话题'
    assert baidu['data']['items'][0]['hot'] == '9999'
    assert baidu['data']['items'][0]['description'] == '话题摘要'
    assert baidu['data']['items'][0]['image'] == 'https://quan1234.com/api/image-proxy?url=https%3A%2F%2Fexample.com%2Fhot.png'
    assert baidu['data']['items'][0]['url'] == 'https://example.com/hot'
    assert baidu['data']['items'][0]['raw']['keyword'] == '百度话题'
    assert baidu['data']['items'][0]['raw']['index'] == '9999'


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
    assert result['data']['platform'] == 'baidu'
    assert result['data']['keyword'] == '微博话题'
    assert result['data']['sourceUrl'] == 'https://s.weibo.com/weibo?q=test'
    assert '微博话题 引发关注' in result['data']['summary']
    assert '网友正在讨论微博话题的最新进展' in result['data']['summary']
    assert '微博话题 引发关注' in result['data']['content']
    assert '网友正在讨论微博话题的最新进展' in result['data']['content']
    assert '通常反映用户短时间内集中搜索' not in result['data']['content']
    assert result['data']['sections']
    assert result['data']['sections'][0]['title'] == '相关新闻内容'
    assert result['data']['relatedNews'][0]['title'] == '微博话题 引发关注'
    assert result['data']['relatedNews'][0]['localUrl'].startswith('/api/news/local/')
    assert DummyNewsDetailService.calls == ['https://example.com/topic']


def test_hot_search_detail_fetches_keyword_news_when_category_feeds_do_not_match():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }
    DummyHttpClient.text_responses = {
        ('https://www.sogou.com/sogou', None): '''
        <div class="vrwrap">
          <h3 class="vr-title"><a href="/link?url=abc">世界杯真正的预言家相关新闻</a></h3>
          <div class="fz-mid space-txt"><span>2026年6月13日-</span>这是一条围绕世界杯出现了真正的预言家的新闻摘要，介绍预测结果和赛后讨论。</div>
          <div class="citeurl"><span>搜狐 - www.sohu.com</span><span class="cite-date">- 2026-6-13</span></div>
        </div>
        '''
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='weibo',
        keyword='世界杯出现了真正的预言家',
        hot='1039923',
        description='',
        url='https://s.weibo.com/weibo?q=test',
    ))

    paths = [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls]
    assert paths[:3] == ['/internet/index', '/esports/index', '/auto/index']
    assert 'https://www.sogou.com/sogou' in paths
    assert result['code'] == 200
    assert result['data']['relatedNews'][0]['title'] == '世界杯真正的预言家相关新闻'
    assert result['data']['relatedNews'][0]['localUrl'].startswith('/api/news/local/')
    assert DummyNewsDetailService.calls == ['https://www.sogou.com/link?url=abc']
    assert '围绕世界杯出现了真正的预言家的新闻摘要' in result['data']['summary']
    assert '围绕世界杯出现了真正的预言家的新闻摘要' in result['data']['content']
    assert '该话题来自微博热搜榜' not in result['data']['content']


def test_hot_search_detail_includes_baidu_raw_result_fields_as_content():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }
    raw = {
        "word": "百度真实热搜",
        "hotScore": "987654",
        "desc": "百度接口返回的真实摘要正文",
        "url": "https://m.baidu.com/s?word=real",
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='百度真实热搜',
        hot='987654',
        description='百度接口返回的真实摘要正文',
        url='https://m.baidu.com/s?word=real',
        raw=json.dumps(raw, ensure_ascii=False),
    ))

    text = result['data']['summary'] + result['data']['content']
    assert result['code'] == 200
    assert '百度接口返回的真实摘要正文' in text
    assert result['data']['sections'][0]['title'] == '百度热搜榜返回信息'
    assert '热度：987654' in result['data']['sections'][0]['body']
    assert result['data']['rawHotItem']['word'] == '百度真实热搜'


def test_baidu_hot_search_merges_official_images_when_nethot_lacks_media():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/nethot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"keyword": "百度话题", "index": "9999", "brief": "话题摘要"}]}},
        ('https://top.baidu.com/api/board', None): {
            "success": True,
            "data": {
                "cards": [{"content": [{"word": "百度话题", "hotScore": "8888", "desc": "官方摘要", "img": "https://fyb-2.cdn.bcebos.com/hotboard_image/demo-image", "url": "https://www.baidu.com/s?wd=official&sa=fyb_news"}]}]
            }
        },
    }

    result = run(TianApiService.get_hot_search('baidu'))

    paths = [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls]
    assert paths == ['/nethot/index', 'https://top.baidu.com/api/board']
    item = result['data']['items'][0]
    assert item['title'] == '百度话题'
    assert item['description'] == '话题摘要'
    assert item['image'] == 'https://quan1234.com/api/image-proxy?url=https%3A%2F%2Ffyb-2.cdn.bcebos.com%2Fhotboard_image%2Fdemo-image'
    assert item['url'] == 'https://www.baidu.com/s?wd=official&sa=fyb_news'


def test_baidu_hot_search_uses_official_baidu_top_when_tianapi_unavailable():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/nethot/index', None): {"code": 150, "msg": "热搜接口暂不可用"},
        ('https://top.baidu.com/api/board', None): {
            "success": True,
            "data": {
                "cards": [{
                    "component": "hotList",
                    "content": [{
                        "index": 0,
                        "word": "百度官方热搜",
                        "query": "百度官方热搜",
                        "hotScore": "7807881",
                        "desc": "来自百度官方热搜榜的摘要",
                        "img": "https://fyb-2.cdn.bcebos.com/hotboard_image/demo-image",
                        "url": "https://www.baidu.com/s?wd=official&sa=fyb_news",
                    }]
                }]
            }
        },
    }

    result = run(TianApiService.get_hot_search('baidu'))

    paths = [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls]
    assert paths == ['/nethot/index', 'https://top.baidu.com/api/board']
    assert result['code'] == 200
    assert result.get('fallback') is not True
    assert result['data']['title'] == '百度热搜榜'
    assert result['data']['items'][0]['rank'] == 1
    assert result['data']['items'][0]['title'] == '百度官方热搜'
    assert result['data']['items'][0]['hot'] == '7807881'
    assert result['data']['items'][0]['description'] == '来自百度官方热搜榜的摘要'
    assert result['data']['items'][0]['image'] == 'https://quan1234.com/api/image-proxy?url=https%3A%2F%2Ffyb-2.cdn.bcebos.com%2Fhotboard_image%2Fdemo-image'
    assert result['data']['items'][0]['url'] == 'https://www.baidu.com/s?wd=official&sa=fyb_news'
    assert result['data']['items'][0]['raw']['word'] == '百度官方热搜'
    assert all(topic not in str(result['data']) for topic in ['今日热点', '民生新闻', '科技动态', '财经观察', '文娱资讯'])


def test_baidu_hot_search_detail_prefers_matching_brief_over_unrelated_news():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": [
            {"title": "滴滴为什么选择做一件反效率的事", "description": "和当前热搜无关的科技新闻", "source": "科技", "url": "https://example.com/didi"},
        ]}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }
    DummyHttpClient.text_responses = {
        ('https://www.sogou.com/sogou', None): '',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='荷兰2比2日本',
        hot='12345',
        description='北京时间6月15日，2026年美加墨世界杯进行F组首轮角逐，荷兰队对阵日本队。',
        url='https://www.baidu.com/s?wd=test',
        raw='{"keyword":"荷兰2比2日本","brief":"北京时间6月15日，2026年美加墨世界杯进行F组首轮角逐，荷兰队对阵日本队。"}',
    ))

    assert result['code'] == 200
    assert result['data']['keyword'] == '荷兰2比2日本'
    assert '荷兰2比2日本' in result['data']['summary']
    assert '世界杯进行F组首轮角逐' in result['data']['summary']
    assert '滴滴为什么选择做一件反效率的事' not in result['data']['summary']
    assert result['data']['relatedNews'] == []


def test_baidu_empty_hot_search_does_not_show_unavailable_message():
    fallback = TianApiService._empty_hot_search('baidu')
    assert fallback['title'] == '百度热搜榜'
    assert fallback['items'] == []
    assert all(topic not in str(fallback) for topic in ['今日热点', '民生新闻', '科技动态', '财经观察', '文娱资讯'])

    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='百度新闻标题',
        hot='12345',
        description='百度接口返回的新闻摘要',
        url='https://m.baidu.com/s?word=real',
        raw='{"word":"百度新闻标题","hotScore":"12345","desc":"百度接口返回的新闻摘要"}',
    ))
    text = result['data']['summary'] + result['data']['content']
    assert result['code'] == 200
    assert '百度新闻标题' in text
    assert '百度接口返回的新闻摘要' in text
    assert '热搜接口暂不可用' not in text
    assert '接口暂不可用' not in text


if __name__ == '__main__':
    setup_module(None)
    for test in [
        test_news_endpoints_use_real_paths_and_normalize_nested_newslist,
        test_gold_endpoint_sends_kinds_and_normalizes_market_fields,
        test_gold_fallback_is_not_renormalized_when_api_key_is_missing,
        test_crude_endpoint_queries_wti_and_blt_and_normalizes_market_fields,
        test_daily_brief_endpoint_uses_bulletin_and_normalizes_lines,
        test_hot_search_endpoint_uses_baidu_nethot_and_normalizes_items,
        test_hot_search_detail_builds_content_from_keyword_and_related_news,
        test_hot_search_detail_fetches_keyword_news_when_category_feeds_do_not_match,
        test_hot_search_detail_includes_baidu_raw_result_fields_as_content,
        test_baidu_hot_search_merges_official_images_when_nethot_lacks_media,
        test_baidu_hot_search_uses_official_baidu_top_when_tianapi_unavailable,
        test_baidu_hot_search_detail_prefers_matching_brief_over_unrelated_news,
        test_baidu_empty_hot_search_does_not_show_unavailable_message,
    ]:
        setup_module(None)
        test()
    print('tianapi service contract tests passed')
