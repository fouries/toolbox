import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const briefPagePath = path.resolve('src/pages/daily-brief/index.vue')
const hotSearchPagePath = path.resolve('src/pages/hot-search/index.vue')
const hotSearchDetailPagePath = path.resolve('src/pages/hot-search-detail/index.vue')
const backendMainPath = path.resolve('../backend/main.py')
const backendTianApiPath = path.resolve('../backend/api/tianapi.py')

for (const file of [briefPagePath, hotSearchPagePath]) {
  assert.ok(fs.existsSync(file), `${path.relative(process.cwd(), file)} should exist`)
}

const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const routes = pagesJson.pages.map(page => page.path)
assert.ok(routes.includes('pages/daily-brief/index'), 'pages.json should register 每日简报 page route')
assert.ok(routes.includes('pages/hot-search/index'), 'pages.json should register 热搜榜 page route')
assert.ok(routes.includes('pages/hot-search-detail/index'), 'pages.json should register 热搜详情 page route')

const home = fs.readFileSync(homePath, 'utf8')
for (const [id, name, route] of [
  ['daily-brief', '每日简报', '/pages/daily-brief/index'],
  ['weibo-hot', '微博热搜榜', '/pages/hot-search/index?platform=weibo'],
  ['baidu-hot', '百度热搜榜', '/pages/hot-search/index?platform=baidu'],
]) {
  assert.match(home, new RegExp(`id:\\s*'${id}'[\\s\\S]*name:\\s*'${name}'[\\s\\S]*path:\\s*'${route.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}'[\\s\\S]*implemented:\\s*true`), `home should enable ${name} tool card`)
}

const api = fs.readFileSync(apiPath, 'utf8')
assert.match(api, /export\s+interface\s+DailyBriefItem/, 'api should expose DailyBriefItem type')
assert.match(api, /export\s+interface\s+HotSearchItem/, 'api should expose HotSearchItem type')
assert.match(api, /image\?:\s*string/, 'HotSearchItem should expose optional image url')
assert.match(api, /getDailyBrief\s*=\s*\(\)/, 'api should expose getDailyBrief()')
assert.match(api, /\/api\/daily-brief/, 'getDailyBrief should call backend daily brief endpoint')
assert.match(api, /getHotSearch\s*=\s*\(platform:/, 'api should expose getHotSearch(platform)')
assert.match(api, /\/api\/hot-search\?platform=\$\{encodeURIComponent\(platform\)\}/, 'getHotSearch should call backend hot search endpoint with platform')
assert.match(api, /export\s+interface\s+HotSearchDetailData/, 'api should expose HotSearchDetailData type')
assert.match(api, /getHotSearchDetail\s*=\s*\(params:/, 'api should expose getHotSearchDetail(params)')
assert.match(api, /\/api\/hot-search\/detail\?\$\{query\}/, 'getHotSearchDetail should call backend hot search detail endpoint')

const briefPage = fs.readFileSync(briefPagePath, 'utf8')
assert.match(briefPage, /每日简报/, 'daily brief page should render title text')
assert.match(briefPage, /getDailyBrief/, 'daily brief page should fetch daily brief API')
assert.match(briefPage, /v-for="item in briefItems"/, 'daily brief page should render brief item list')
assert.match(briefPage, /刷新简报/, 'daily brief page should provide a refresh action')

const hotSearchPage = fs.readFileSync(hotSearchPagePath, 'utf8')
assert.match(hotSearchPage, /微博热搜榜|百度热搜榜/, 'hot search page should support weibo and baidu labels')
assert.doesNotMatch(hotSearchPage, /title: '百度热搜'[^榜]/, 'baidu tab should be labelled 百度热搜榜')
assert.match(hotSearchPage, /getHotSearch/, 'hot search page should fetch hot search API')
assert.match(hotSearchPage, /platformTabs/, 'hot search page should provide platform tabs')
assert.match(hotSearchPage, /v-for="item in displayedHotItems"/, 'hot search page should render capped display item list')
assert.match(hotSearchPage, /displayedHotItems\s*=\s*computed\(\(\)\s*=>[\s\S]*activePlatform\.value\s*===\s*'baidu'[\s\S]*hotItems\.value\.slice\(0,\s*50\)/, 'baidu hot search list should cap display to 50 items')
assert.match(hotSearchPage, /shouldShowHotDescription\s*=\s*computed\(\(\)\s*=>\s*activePlatform\.value\s*!==\s*'baidu'\)/, 'baidu hot search list should show only titles, not descriptions')
assert.match(hotSearchPage, /<view\s+class="hot-body"\s+v-if="shouldShowHotImage\(item\)"[\s\S]*<image\s+class="hot-image"[\s\S]*:src="item\.image"[\s\S]*mode="aspectFill"/, 'baidu hot search images should be laid out in the body content area')
assert.match(hotSearchPage, /<view class="hot-main">[\s\S]*<text class="hot-title">\{\{ item\.title \}\}<\/text>[\s\S]*<view\s+class="hot-body"\s+v-if="shouldShowHotImage\(item\)"/, 'hot search images should appear inside the main body after the title, not in the title row')
assert.doesNotMatch(hotSearchPage, /<text class="hot-rank"[\s\S]*<image\s+class="hot-image"[\s\S]*<view class="hot-main">/, 'hot search images should not be rendered as title-row thumbnails')
assert.match(hotSearchPage, /\.hot-body\s*\{[\s\S]*margin-top:\s*14rpx;[\s\S]*display:\s*block;/, 'hot search image body should be a block area under the title')
assert.match(hotSearchPage, /\.hot-image\s*\{[\s\S]*width:\s*100%;[\s\S]*height:\s*240rpx;[\s\S]*object-fit:\s*cover;/, 'hot search body image should be a full-width tiled image, not a compact thumbnail')
assert.match(hotSearchPage, /v-if="shouldShowHotDescription && item\.description"/, 'hot search descriptions should be hidden for baidu hot search')
assert.match(hotSearchPage, /@tap="openHotDetail\(item\)"/, 'hot search items should navigate to native detail page')
assert.match(hotSearchPage, /uni\.navigateTo\(\{[\s\S]*\/pages\/hot-search-detail\/index\?/, 'hot search item tap should use internal detail route')
assert.match(hotSearchPage, /encodeURIComponent\(item\.title\)/, 'hot search detail route should encode title')
assert.match(hotSearchPage, /raw=\$\{encodeURIComponent\(JSON\.stringify\(item\.raw \|\| item\)\)\}/, 'hot search detail route should pass the raw hot-search API item')
assert.doesNotMatch(hotSearchPage, /@tap="copyHotLink\(item\)"/, 'hot search list should not only copy links on item tap')
assert.match(hotSearchPage, /onLoad/, 'hot search page should read platform from route query')

const hotSearchDetailPage = fs.readFileSync(hotSearchDetailPagePath, 'utf8')
assert.match(hotSearchDetailPage, /热搜详情/, 'hot search detail page should render title text')
assert.match(hotSearchDetailPage, /keyword/, 'hot search detail page should read keyword from route query')
assert.match(hotSearchDetailPage, /getHotSearchDetail/, 'hot search detail page should fetch backend detail content')
assert.match(hotSearchDetailPage, /rawHotData/, 'hot search detail page should forward the raw hot-search API item')
assert.match(hotSearchDetailPage, /detail\.summary/, 'hot search detail page should render backend summary')
assert.match(hotSearchDetailPage, /v-for="section in detail\.sections"/, 'hot search detail page should render backend content sections')
assert.match(hotSearchDetailPage, /copyHotLink/, 'hot search detail page should keep copy-link fallback')
assert.match(hotSearchDetailPage, /openNewsDetail/, 'hot search detail page should navigate related news to native news detail')
assert.match(hotSearchDetailPage, /\/pages\/news-detail\/index\?url=\$\{encodeURIComponent\(safeUrl\)\}/, 'related news should use native news detail route')

const backendMain = fs.readFileSync(backendMainPath, 'utf8')
const backendTianApi = fs.readFileSync(backendTianApiPath, 'utf8')
assert.match(backendMain, /@app\.get\("\/api\/daily-brief"/, 'backend should expose /api/daily-brief')
assert.match(backendMain, /TianApiService\.get_daily_brief/, 'daily brief endpoint should call TianApi service')
assert.match(backendMain, /@app\.get\("\/api\/hot-search"/, 'backend should expose /api/hot-search')
assert.match(backendMain, /TianApiService\.get_hot_search/, 'hot search endpoint should call TianApi service')
assert.match(backendMain, /@app\.get\("\/api\/hot-search\/detail"/, 'backend should expose /api/hot-search/detail')
assert.match(backendMain, /TianApiService\.get_hot_search_detail/, 'hot search detail endpoint should call TianApi service')
assert.match(backendTianApi, /get_daily_brief/, 'TianApi service should implement daily brief fetcher')
assert.match(backendTianApi, /"\/bulletin\/index"/, 'daily brief should use TianAPI /bulletin/index endpoint')
assert.match(backendTianApi, /get_hot_search/, 'TianApi service should implement hot search fetcher')
assert.match(backendTianApi, /"weibo":\s*"\/weibohot\/index"/, 'weibo hot search should use TianAPI /weibohot/index endpoint')
assert.match(backendTianApi, /"baidu":\s*"\/baiduhot\/index"/, 'baidu hot search should use TianAPI /baiduhot/index endpoint')
assert.match(backendTianApi, /百度热搜榜/, 'backend should label baidu hot search as 百度热搜榜')
assert.doesNotMatch(backendTianApi, /\("今日热点"/, 'baidu hot search should not expose category fallback topics')
assert.match(backendTianApi, /_empty_hot_search/, 'backend should return an empty list instead of fake baidu topics when upstream fails')
assert.match(backendTianApi, /rawHotItem/, 'hot search detail should include the raw hot-search API item in the response')

console.log('daily brief and hot search features are valid')
