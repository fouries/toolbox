import asyncio
import json

from api.tianapi import TianApiService


class DummyNewsDetailService:
    calls = []

    @staticmethod
    def _is_safe_url(url):
        return str(url or '').startswith('http')

    @staticmethod
    async def fetch_detail(url, preferred_image=""):
        DummyNewsDetailService.calls.append(url)
        local_id = str(abs(hash(url)))[:8]
        return {"code": 200, "data": {"localId": local_id, "localUrl": f"/api/news/local/{local_id}", "description": "本地化后的新闻正文摘要", "images": []}}


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
        query_value = (params or {}).get('code') or (params or {}).get('q') or (params or {}).get('query') or (params or {}).get('word') or (params or {}).get('wd')
        key = (path, query_value)
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
    assert all(call[1].get('num') == '20' for call in DummyHttpClient.calls)
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
        ('/nethot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"keyword": "百度话题", "index": "9999", "brief": "话题摘要正文", "trend": "沸", "picUrl": "https://example.com/hot.png", "url": "https://example.com/hot"}]}},
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
    assert baidu['data']['items'][0]['description'] == '话题摘要正文'
    assert baidu['data']['items'][0]['image'] == 'https://quan1234.com/api/image-proxy?url=https%3A%2F%2Fexample.com%2Fhot.png'
    assert baidu['data']['items'][0]['url'] == 'https://example.com/hot'
    assert baidu['data']['items'][0]['raw']['keyword'] == '百度话题'
    assert baidu['data']['items'][0]['raw']['index'] == '9999'


def test_hot_search_detail_basic_uses_only_payload_fields_for_fast_first_paint():
    DummyHttpClient.calls = []
    raw = {
        "word": "百度轻详情",
        "hotScore": "123456",
        "desc": "列表携带的摘要正文",
        "url": "https://m.baidu.com/s?word=fast",
    }

    result = run(TianApiService.get_hot_search_detail_basic(
        platform='baidu',
        keyword='百度轻详情',
        hot='123456',
        description='列表携带的摘要正文',
        url='https://m.baidu.com/s?word=fast',
        raw=json.dumps(raw, ensure_ascii=False),
    ))

    assert DummyHttpClient.calls == []
    assert result['code'] == 200
    assert result['data']['keyword'] == '百度轻详情'
    assert result['data']['summary'] == '列表携带的摘要正文'
    assert result['data']['videos'] == []
    assert result['data']['images'] == []
    assert result['data']['relatedNews'] == []


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

    paths = [call[0].replace('https://apis.tianapi.com', '') for call in DummyHttpClient.calls]
    assert paths[:3] == ['/internet/index', '/esports/index', '/auto/index']
    assert 'https://m.baidu.com/s' in paths
    assert result['code'] == 200
    assert result['data']['platform'] == 'baidu'
    assert result['data']['keyword'] == '微博话题'
    assert result['data']['sourceUrl'] == 'https://s.weibo.com/weibo?q=test'
    # summary只包含description，不包含标题
    assert '网友正在讨论微博话题的最新进展' in result['data']['summary']
    assert '微博话题 引发关注' not in result['data']['summary']
    assert '微博话题 引发关注' in result['data']['content']
    assert '网友正在讨论微博话题的最新进展' in result['data']['content']
    assert '通常反映用户短时间内集中搜索' not in result['data']['content']
    assert result['data']['sections']
    assert result['data']['sections'][0]['title'] == '相关新闻内容'
    assert result['data']['relatedNews'][0]['title'] == '微博话题 引发关注'
    assert result['data']['relatedNews'][0]['url'] == 'https://example.com/topic'
    assert DummyNewsDetailService.calls == []


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
    assert result['data']['relatedNews'][0]['url'] == 'https://www.sogou.com/link?url=abc'
    assert DummyNewsDetailService.calls == []
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
        ('/nethot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"keyword": "百度话题", "index": "9999", "brief": "话题摘要正文"}]}},
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
    assert item['description'] == '话题摘要正文'
    assert item['image'] == 'https://quan1234.com/api/image-proxy?url=https%3A%2F%2Ffyb-2.cdn.bcebos.com%2Fhotboard_image%2Fdemo-image'
    assert item['url'] == 'https://www.baidu.com/s?wd=official&sa=fyb_news'


def test_baidu_hot_search_replaces_truncated_nethot_summary_with_official_desc():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('/nethot/index', None): {"code": 200, "msg": "success", "result": {"list": [{"keyword": "1分钱外卖要凉了", "index": "9999", "brief": "外卖平台脱离正常促销范畴的长期、大额补贴活动，将迎来监管红线。市场监管总局发布的《外卖平台补贴行为规范十条（征求意见稿）》明确，外卖平台不得以长期、... 查看更多&gt;", "picUrl": "https://example.com/hot.png", "url": "https://www.baidu.com/s?wd=nethot"}]}},
        ('https://top.baidu.com/api/board', None): {
            "success": True,
            "data": {
                "cards": [{"content": [{"word": "1分钱外卖要凉了", "hotScore": "8888", "desc": "外卖平台脱离正常促销范畴的长期、大额补贴活动，将迎来监管红线。市场监管总局发布的《外卖平台补贴行为规范十条（征求意见稿）》明确，外卖平台不得以长期、大额补贴扰乱市场秩序。", "img": "https://fyb-2.cdn.bcebos.com/hotboard_image/demo-image", "url": "https://www.baidu.com/s?wd=official&sa=fyb_news"}]}]
            }
        },
    }

    result = run(TianApiService.get_hot_search('baidu'))

    item = result['data']['items'][0]
    assert item['description'].endswith('不得以长期、大额补贴扰乱市场秩序。')
    assert '查看更多' not in item['description']
    assert '...' not in item['description']


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


def test_baidu_hot_search_detail_completes_truncated_summary_from_related_news():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('https://top.baidu.com/api/board', None): {"success": True, "data": {"cards": [{"content": []}]}},
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": [
            {"title": "瑞士外交部证实美伊会谈取消", "description": "瑞士外交部19日证实美国和伊朗原定当日在瑞士举行的会谈取消。", "source": "新华社", "url": "https://example.com/swiss"},
        ]}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='瑞士外交部证实美伊会谈取消',
        hot='12345',
        description='瑞士外交部19日证实美国和伊朗原定当日在瑞士举行的... 查看更多&gt;',
        url='https://www.baidu.com/s?wd=real&sa=fyb_news',
        raw='{"word":"瑞士外交部证实美伊会谈取消","desc":"瑞士外交部19日证实美国和伊朗原定当日在瑞士举行的... 查看更多&gt;"}',
    ))

    assert result['code'] == 200
    assert result['data']['summary'].startswith('瑞士外交部19日证实美国和伊朗原定当日在瑞士举行的会谈取消。')
    assert '查看更多' not in result['data']['summary']
    assert '...' not in result['data']['summary']


def test_baidu_hot_search_detail_filters_incomplete_related_news_content():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('https://top.baidu.com/api/board', None): {"success": True, "data": {"cards": [{"content": []}]}},
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }
    DummyHttpClient.text_responses = {
        ('https://www.sogou.com/sogou', '工信部辟谣8家车企被撤销资质'): '',
        ('https://www.bing.com/search', '工信部辟谣8家车企被撤销资质'): '''
        <li class="b_algo">
          <h2><a href="https://www.sohu.com/a/1038271640_114984"><strong>工信部辟谣</strong>：<strong>8家车企被撤销</strong>生产<strong>资质</strong>为不实信息_搜狐汽车 ...</a></h2>
          <div class="b_caption"><p>1 天前&ensp;&#0183;&ensp;工信部方面表示，网传被撤销生产资质的8家企业，仅原一汽夏利多年前已注销准入许可；其余7家企业中，仅部分企业已注销或拟注销个别生产地址，并非整车生产资质被注销。 网传信息来源不明，缺乏任何官方依据。</p></div>
          <cite>https://www.sohu.com/a/1038271640_114984</cite>
        </li>
        <li class="b_algo">
          <h2><a href="https://example.com/bad">8家车企被撤销生产资质？消息是假的</a></h2>
          <div class="b_caption"><p>前日,网传“工信部第408批公告将一汽夏利、华晨自主、众泰、猎豹、力帆等8家汽车企业移出车企名录”。6月17日,经多家正规媒体向工...</p></div>
        </li>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='工信部辟谣8家车企被撤销资质',
        hot='6851511',
        description='近日，针对“8家车企被移出名录、整车生产资质永久失效”的网传消息，工信部回应称相关说法不实。除一汽夏利早年已注销准入许可外，其余车企仍在名录中，部分... 查看更多&gt;',
        url='https://m.baidu.com/s?word=real&sa=fyb_news',
        raw='{"word":"工信部辟谣8家车企被撤销资质"}',
    ))

    content = result['data']['content']
    assert '并非整车生产资质被注销。' in content
    assert '8家车企被撤销生产资质？消息是假的' not in content
    assert '8家车企被 冻结生产 资质 众泰 辟谣 :不实信息' not in content
    assert '工...' not in content
    assert '为不...' not in content
    assert '消息...' not in content
    assert '查看更多' not in content


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
    # summary只包含description，不包含关键词前缀
    assert '北京时间6月15日，2026年美加墨世界杯进行F组首轮角逐' in result['data']['summary']
    assert '荷兰2比2日本' not in result['data']['summary']
    assert '滴滴为什么选择做一件反效率的事' not in result['data']['summary']
    assert result['data']['relatedNews'] == []


def test_baidu_hot_search_detail_extracts_video_resources_from_search_html():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://m.baidu.com/s', None): '''
        <script>
        window.tplData={"videoData":{"autoplayInfo":{"video":{
          "poster":"https://t14.baidu.com/poster.jpg",
          "src":"https://vd3.bdstatic.com/mda-demo/540p/h264/demo.mp4?authorization=test",
          "videoInfo":{"clarityUrl":[{"url":"https://vd3.bdstatic.com/mda-demo/540p/h264/demo.mp4?authorization=test"}]}
        }}},"contentData":{}}
        </script>
        '''
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='叠滘龙船漂移',
        hot='12345',
        description='百度接口返回的新闻摘要',
        url='https://m.baidu.com/s?word=real',
        raw='{"word":"叠滘龙船漂移","desc":"百度接口返回的新闻摘要"}',
    ))

    assert result['code'] == 200
    assert result['data']['videos'][0]['url'] == 'https://quan1234.com/api/video-proxy?url=https%3A%2F%2Fvd3.bdstatic.com%2Fmda-demo%2F540p%2Fh264%2Fdemo.mp4%3Fauthorization%3Dtest'
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd3.bdstatic.com/mda-demo/540p/h264/demo.mp4?authorization=test'
    assert result['data']['videos'][0]['poster'] == 'https://t14.baidu.com/poster.jpg'


def test_baidu_hot_search_detail_falls_back_to_haokan_video_pages():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '''
        <a data-mdurl="https://haokan.baidu.com/v?pd=wisenatural&vid=6169387791737944912">今年端午60年一遇 好看视频</a>
        ''',
        ('https://m.baidu.com/s', None): '<html>百度安全验证</html>',
        ('https://haokan.baidu.com/v?pd=wisenatural&vid=6169387791737944912', None): '''
        <title>今年端午节，60年不遇,好看视频</title>
        <script>{"curVideoMeta":{"title":"今年端午节，60年不遇","clarityUrl":[
          {"rank":0,"title":"标清","url":"https:\\/\\/vd4.bdstatic.com\\/mda-demo\\/cae_h264\\/demo.mp4?auth_key=test"},
          {"rank":1,"title":"高清","url":"https:\\/\\/vd4.bdstatic.com\\/mda-demo\\/hd\\/cae_h264\\/demo.mp4?auth_key=test"}
        ]}}</script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='今年端午60年一遇',
        hot='12345',
        description='快接住60年一遇的端午好运！',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"今年端午60年一遇","desc":"快接住60年一遇的端午好运！"}',
    ))

    assert result['code'] == 200
    assert len(result['data']['videos']) == 1
    assert result['data']['videos'][0]['url'] == 'https://quan1234.com/api/video-proxy?url=https%3A%2F%2Fvd4.bdstatic.com%2Fmda-demo%2Fcae_h264%2Fdemo.mp4%3Fauth_key%3Dtest'
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd4.bdstatic.com/mda-demo/cae_h264/demo.mp4?auth_key=test'
    called_urls = [call[0] for call in DummyHttpClient.calls]
    assert 'https://www.so.com/s' not in called_urls
    assert 'https://www.sogou.com/web' not in called_urls


def test_baidu_hot_search_detail_does_not_use_generic_search_video_results():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html>百度安全验证</html>',
        ('https://m.baidu.com/s', None): '<html>百度安全验证</html>',
        ('https://www.so.com/s', None): '''
        <a data-mdurl="https://haokan.baidu.com/v?pd=wisenatural&vid=wrong">相似但不是原链接视频</a>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='今年端午60年一遇',
        hot='12345',
        description='快接住60年一遇的端午好运！',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"今年端午60年一遇","desc":"快接住60年一遇的端午好运！"}',
    ))

    assert result['code'] == 200
    assert result['data']['videos'] == []
    called_urls = [call[0] for call in DummyHttpClient.calls]
    assert 'https://www.so.com/s' not in called_urls
    assert 'https://www.sogou.com/web' not in called_urls


def test_baidu_hot_search_detail_uses_mobile_vsearch_when_source_hits_safety_check():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html><title>百度安全验证</title></html>',
        ('https://www.baidu.com/s', 'real'): '<html><title>百度安全验证</title></html>',
        ('https://m.baidu.com/s', None): '<html><title>百度安全验证</title></html>',
        ('https://m.baidu.com/sf/vsearch', 'real'): '''
        <script>window.pageData={"title":"顶流演员也没戏拍了？刘亦菲超900天没进组，董子健刘昊然在线求工作",
          "loc":"https://haokan.baidu.com/v?pd=wisenatural&vid=12641358385028720826",
          "videoSrc":"https://vd3.bdstatic.com/mda-real/hd/cae_h264/demo.mp4?pd=19&vt=1",
          "previewProps":{"poster":"http://t15.baidu.com/it/u=480050288,1670784519&fm=225"}}
        </script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='顶流演员竟然没戏拍了吗',
        hot='7808291',
        description='多位演员集体求职。',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"顶流演员竟然没戏拍了吗","desc":"多位演员集体求职。"}',
    ))

    assert result['code'] == 200
    assert len(result['data']['videos']) == 1
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd3.bdstatic.com/mda-real/hd/cae_h264/demo.mp4?pd=19&vt=1'
    assert result['data']['videos'][0]['poster'] == 'http://t15.baidu.com/it/u=480050288,1670784519&fm=225'
    calls = {(call[0], tuple(sorted((call[1] or {}).items()))) for call in DummyHttpClient.calls}
    assert ('https://m.baidu.com/sf/vsearch', (('atn', 'index'), ('pd', 'video'), ('tn', 'vsearch'), ('word', 'real'))) in calls


def test_baidu_hot_search_detail_rejects_unmatched_mobile_vsearch_video():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html><title>百度安全验证</title></html>',
        ('https://www.baidu.com/s', 'real'): '<html><title>百度安全验证</title></html>',
        ('https://m.baidu.com/s', None): '<html><title>百度安全验证</title></html>',
        ('https://m.baidu.com/sf/vsearch', 'real'): '''
        <script>window.pageData={"title":"完全无关的娱乐短视频",
          "loc":"https://haokan.baidu.com/v?pd=wisenatural&vid=wrong",
          "videoSrc":"https://vd3.bdstatic.com/mda-wrong/hd/cae_h264/demo.mp4?pd=19&vt=1"}
        </script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='顶流演员竟然没戏拍了吗',
        hot='7808291',
        description='多位演员集体求职。',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"顶流演员竟然没戏拍了吗","desc":"多位演员集体求职。"}',
    ))

    assert result['code'] == 200
    assert result['data']['videos'] == []


def test_baidu_hot_search_detail_does_not_use_baidu_video_vertical_as_source():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html>百度安全验证</html>',
        ('https://www.baidu.com/s', None): '''
        <div class="result" mu="https://haokan.baidu.com/v?pd=wisenatural&vid=6169387791737944912">
            今年端午60年一遇 普通搜索页视频
        </div>
        ''',
        ('https://m.baidu.com/s', None): '<html>百度安全验证</html>',
        ('https://haokan.baidu.com/v?pd=wisenatural&vid=6169387791737944912', None): '''
        <title>今年端午60年一遇，普通搜索页视频,好看视频</title>
        <script>{"curVideoMeta":{"title":"今年端午60年一遇，普通搜索页视频","clarityUrl":[
          {"rank":0,"title":"标清","url":"https:\\/\\/vd5.bdstatic.com\\/mda-demo\\/cae_h264\\/demo.mp4?auth_key=test"}
        ]}}</script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='今年端午60年一遇',
        hot='12345',
        description='快接住60年一遇的端午好运！',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"今年端午60年一遇","desc":"快接住60年一遇的端午好运！"}',
    ))

    assert result['code'] == 200
    assert len(result['data']['videos']) == 1
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd5.bdstatic.com/mda-demo/cae_h264/demo.mp4?auth_key=test'
    calls = {(call[0], tuple(sorted((call[1] or {}).items()))) for call in DummyHttpClient.calls}
    assert ('https://www.baidu.com/s', (('pd', 'video'), ('tn', 'vsearch'), ('wd', '今年端午60年一遇'))) not in calls
    assert ('https://www.baidu.com/s', (('tn', 'baiduhome_pg'), ('wd', 'real'))) in calls


def test_baidu_hot_search_detail_extracts_baidu_video_landing_pages():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html>百度安全验证</html>',
        ('https://www.baidu.com/s', 'real'): '''
        <script>{"src":"https://mbd.baidu.com/newspage/data/videolanding?nid=sv_3221883602623471607"}</script>
        ''',
        ('https://m.baidu.com/s', None): '<html>百度安全验证</html>',
        ('https://mbd.baidu.com/newspage/data/videolanding?nid=sv_3221883602623471607', None): '''
        <script>window.jsonData={"curVideoMeta":{"title":"缅甸总统敏昂莱抵达宇树科技，机器人现场演示写毛笔字","clarityUrl":[
          {"rank":0,"title":"标清","url":"https:\\/\\/vd3.bdstatic.com\\/mda-unitree\\/540p\\/h264_cae\\/demo.mp4?v_from_s=bdapp-resbox-hnb"},
          {"rank":2,"title":"超清","url":"https:\\/\\/vd3.bdstatic.com\\/mda-unitree\\/720p_frame30\\/h264_cae\\/demo.mp4?v_from_s=bdapp-resbox-hnb"}
        ]}}</script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='宇树机器人在缅甸总统面前秀书法',
        hot='7714660',
        description='缅甸总统参观宇树科技，机器人现场书写书法展示科技成果。',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"宇树机器人在缅甸总统面前秀书法","desc":"缅甸总统参观宇树科技。"}',
    ))

    assert result['code'] == 200
    assert len(result['data']['videos']) == 1
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd3.bdstatic.com/mda-unitree/540p/h264_cae/demo.mp4?v_from_s=bdapp-resbox-hnb'
    assert result['data']['videos'][0]['url'].startswith('https://quan1234.com/api/video-proxy?url=')


def test_baidu_hot_search_detail_accepts_near_match_original_haokan_video():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {}
    DummyHttpClient.text_responses = {
        ('https://www.baidu.com/s?wd=real', None): '<html>百度安全验证</html>',
        ('https://www.baidu.com/s', None): '''
        <div class="result" mu="https://haokan.baidu.com/v?pd=wisenatural&vid=12641358385028720826">
            顶流演员竟然没戏拍了吗 百度普通搜索视频
        </div>
        ''',
        ('https://m.baidu.com/s', None): '<html>百度安全验证</html>',
        ('https://haokan.baidu.com/v?pd=wisenatural&vid=12641358385028720826', None): '''
        <title>顶流演员也没戏拍了？刘亦菲超900天没进组，董子健刘昊然在线求工作,好看视频</title>
        <script>{"curVideoMeta":{"title":"顶流演员也没戏拍了？刘亦菲超900天没进组，董子健刘昊然在线求工作","poster":"https:\\/\\/f7.baidu.com\\/poster.jpg","clarityUrl":[
          {"rank":0,"title":"标清","url":"https:\\/\\/vd2.bdstatic.com\\/mda-demo\\/cae_h264\\/demo.mp4?auth_key=test"}
        ]}}</script>
        ''',
    }

    result = run(TianApiService.get_hot_search_detail(
        platform='baidu',
        keyword='顶流演员竟然没戏拍了吗',
        hot='7808291',
        description='多位有作品、有知名度、有资源的演员集体将颁奖礼变成了大型求职现场。',
        url='https://www.baidu.com/s?wd=real',
        raw='{"word":"顶流演员竟然没戏拍了吗","desc":"多位演员集体求职。"}',
    ))

    assert result['code'] == 200
    assert len(result['data']['videos']) == 1
    assert result['data']['videos'][0]['originalUrl'] == 'https://vd2.bdstatic.com/mda-demo/cae_h264/demo.mp4?auth_key=test'
    assert result['data']['videos'][0]['url'].startswith('https://quan1234.com/api/video-proxy?url=')


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


def test_baidu_hot_search_detail_extracts_long_image_from_matching_news_detail():
    DummyHttpClient.calls = []
    DummyHttpClient.responses = {
        ('https://top.baidu.com/api/board', None): {"success": True, "data": {"cards": [{"content": []}]}},
        ('/internet/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
        ('/esports/index', None): {"code": 200, "msg": "success", "result": {"list": []}},
        ('/auto/index', None): {"code": 200, "msg": "success", "result": {"newslist": []}},
    }
    DummyHttpClient.text_responses = {
        ('https://www.sogou.com/sogou', '总书记引屈原诗话家国情'): '''
        <div class="vrwrap">
          <h3 class="vr-title"><a href="https://www.xinhuanet.com/politics/20260619/demo/c.html">学习新语·端午丨总书记引屈原诗话家国情</a></h3>
          <div class="fz-mid space-txt">统筹：黄庆华 苏晓洲 文案：郭洁宇 设计：马发展 新华社新媒体中心、湖南分社联合制作 新华社出品</div>
          <div class="citeurl"><span>新华网</span></div>
        </div>
        ''',
    }
    original_fetch_detail = DummyNewsDetailService.fetch_detail

    async def fetch_detail(url, preferred_image=""):
        DummyNewsDetailService.calls.append(url)
        return {"code": 200, "data": {"images": ["https://quan1234.com/api/news/image-proxy?url=https%3A%2F%2Fwww.xinhuanet.com%2Flong.png"]}}

    DummyNewsDetailService.fetch_detail = staticmethod(fetch_detail)
    try:
        result = run(TianApiService.get_hot_search_detail(
            platform='baidu',
            keyword='总书记引屈原诗话家国情',
            hot='7904134',
            description='节分端午自谁言，万古传闻为屈原。爱国诗人屈原的精神气节，始终感召着中华儿女。习近平总书记曾在多个场合引用屈原诗作名句阐述思想、寄情言志。一起重温这些... 查看更多&gt;',
            url='https://m.baidu.com/s?word=real&sa=fyb_news',
            raw='{"word":"总书记引屈原诗话家国情"}',
        ))
    finally:
        DummyNewsDetailService.fetch_detail = original_fetch_detail

    assert result['code'] == 200
    assert result['data']['images'] == ['https://quan1234.com/api/news/image-proxy?url=https%3A%2F%2Fwww.xinhuanet.com%2Flong.png']
    assert '节分端午自谁言' in result['data']['summary']
    assert result['data']['summary'].startswith('统筹') is False


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
        test_baidu_hot_search_replaces_truncated_nethot_summary_with_official_desc,
        test_baidu_hot_search_uses_official_baidu_top_when_tianapi_unavailable,
        test_baidu_hot_search_detail_completes_truncated_summary_from_related_news,
        test_baidu_hot_search_detail_filters_incomplete_related_news_content,
        test_baidu_hot_search_detail_prefers_matching_brief_over_unrelated_news,
        test_baidu_hot_search_detail_extracts_video_resources_from_search_html,
        test_baidu_hot_search_detail_falls_back_to_haokan_video_pages,
        test_baidu_hot_search_detail_does_not_use_generic_search_video_results,
        test_baidu_hot_search_detail_uses_mobile_vsearch_when_source_hits_safety_check,
        test_baidu_hot_search_detail_rejects_unmatched_mobile_vsearch_video,
        test_baidu_hot_search_detail_does_not_use_baidu_video_vertical_as_source,
        test_baidu_hot_search_detail_extracts_baidu_video_landing_pages,
        test_baidu_hot_search_detail_accepts_near_match_original_haokan_video,
        test_baidu_empty_hot_search_does_not_show_unavailable_message,
        test_baidu_hot_search_detail_extracts_long_image_from_matching_news_detail,
    ]:
        setup_module(None)
        test()
    print('tianapi service contract tests passed')
